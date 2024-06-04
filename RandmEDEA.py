from pyroborobo import Pyroborobo, Controller
import numpy as np

class MedeaController(Controller):

    def __init__(self, wm):
        super().__init__(wm)
        self.gList = dict()
        self.rob = Pyroborobo.get()
        self.next_gen_every_it = 600
        self.wait = 100
        self.ditch = 25
        self.deactivated = False
        self.next_gen_in_it = self.next_gen_every_it
        self.genome = []
        self.seek = True
        self.avoid = False
        self.weights = None
        self.lastX, self.lastY = [0,0]
        self.dropZoneX, self.dropZoneY = np.array(self.rob.arena_size) *0.65
        self.foods = set()
        self.lastObj = None
        self.skipSteps = 5
        self.checkHook = 50

    def reset(self):
        if self.genome == []:
            initCol = np.random.randint(9) % 3
            if initCol == 0: 
                self.genome = [255,0,0]
                self.weights = np.random.uniform(-1, 0.25, self.nb_inputs())
            elif initCol == 1: 
                self.genome = [0,255,0]
                self.weights = np.random.uniform(-0.5, 0.5, self.nb_inputs())
            elif initCol == 2: 
                self.genome = [0,0,255]
                self.weights = np.random.uniform(-0.25, 1, self.nb_inputs())
            self.set_color(*self.genome)
        self.seek = True

    def step(self):
        self.next_gen_in_it -= 1
        if self.deactivated:
            self.set_color(0, 0, 0)
            self.set_translation(0)
            self.set_rotation(0)
            if self.lastObj is not None:
                if not self.lastObj.inZone(): self.removeAnchor()
        
        elif self.next_gen_in_it < 3:
            self.new_generation()
            #self.next_gen_in_it = self.next_gen_every_it

        else:
            # Movement
            self.set_translation(1)
            if self.avoid:
                self.leave()
                if self.ditch <=0:
                    self.removeAnchor()
                    self.seek = True
                    self.avoid = False
                    self.ditch = 25
            elif self.seek:
                self.find() #cam = self.find()
                #if self.inZone():
                #    self.leave()
                #    self.ditch = 25
            else:
                self.seek = self.drop()
                if self.wait <=0 :
                    self.avoid = True
                    self.wait = 100
            # Share weights
            self.broadcast()

    def removeAnchor(self):
        self.lastObj.removeAnchor(self.get_id())
        self.lastObj = None
        

    def leave(self):
        camera_dist = self.get_all_distances()
        if camera_dist[2] < 1:
            self.set_rotation(np.random.choice([-1, 1]))
        elif camera_dist[3] < 1:
            self.set_rotation(-1)
        elif camera_dist[1] < 1:
            self.set_rotation(1)
        else: self.set_rotation(0)
        self.ditch-=1

    def drop(self):
        objID = self.lastObj.get_id()
        if not self.lastObj.inZone():
            self.skipSteps -= 1
            self.checkHook -= 1
            if self.lastX == self.absolute_position[0] and self.lastY == self.absolute_position[1]:
                self.wait -=1
            else: 
                self.wait = 100

            if self.lastObj.type ==1:
                if (self.get_object_at(1)-1 != objID and self.get_object_at(1) != -1) or (self.get_wall_at(0) or self.get_wall_at(1)):
                    self.set_rotation(0.5)
                elif (self.get_object_at(3)-1 != objID and self.get_object_at(3) != -1) or (self.get_wall_at(4) or self.get_wall_at(3)):
                    self.set_rotation(-0.5)
                
            if not self.navigate(objID): return True
            if self.skipSteps <= 0:
                self.lastX, self.lastY = self.absolute_position
                self.skipSteps = 5
            return False
        else: 
            self.foods.add(objID)
            return True

    def eulogy(self):
        id = str(self.get_id())
        foods = str(self.foods)
        suitors = str(list(self.gList.keys()))
        colour = str(self.genome)
        return f"""\nRobot: {id}\
            \nTotal resources """ + str(len(self.foods)) + f""": {foods}\
            \nTotal suitors """ + str(len(self.gList)) + f""": {suitors}\
            \nColour: {colour}\n"""

    def navigate(self, objID):
        orient = self.get_closest_landmark_orientation()
        if orient >= 0.25:
            self.set_rotation(0.125)
            if self.get_object_at(2)-1 == objID:
                self.set_rotation(0)
            elif self.get_object_at(1)-1 == objID:
                self.set_rotation(-0.25)
            elif self.get_object_at(3)-1 == objID:
                self.set_rotation(0.25)
        elif orient <= -0.25:
            self.set_rotation(-0.125)
            if self.get_object_at(2)-1 == objID:
                self.set_rotation(0)
            elif self.get_object_at(3)-1 == objID:
                self.set_rotation(0.25)
            elif self.get_object_at(1)-1 == objID:
                self.set_rotation(-0.25)
        else:
            self.set_rotation(orient)
            if self.get_object_at(3)-1 == objID:
                self.set_rotation(0.125)
            elif self.get_object_at(1)-1 == objID:
                self.set_rotation(-0.125)
            
            if self.checkHook <= 0:
                if self.get_object_at(2)-1 != objID and self.get_object_at(3)-1 != objID and self.get_object_at(1)-1 != objID\
                    and self.euclidean(self.absolute_position, self.lastObj.position)>35:
                    self.removeAnchor()
                    self.checkHook = 50
                    return False
        return True
            
    def isTaken(self, sensr):
        obj = self.get_object_instance_at(sensr)
        if obj is None: return True
        return obj.taken(self.get_id())

    def find(self):
        camera_dist = self.get_all_distances()
        if camera_dist[1] < 1:  # if we see something on our left
            if (self.get_object_at(1) != -1 and not self.isTaken(1) and not self.inZone()):# or collab:  # And it is food
                self.set_rotation(-0.5)  # turn left
                return 1
            else: 
                self.set_rotation(0.5)
        elif camera_dist[3] < 1:  # Otherwise, if we see something on our right
            if (self.get_object_at(3) != -1 and not self.isTaken(3) and not self.inZone()):# or collab:
                self.set_rotation(0.5)  # turn right
                return 3
            else: 
                self.set_rotation(-0.5)
        elif camera_dist[2] < 1:  # if we see something in front of us
            if (self.get_object_at(2) != -1 and not self.isTaken(2) and not self.inZone()):# or collab:  # If we are not avoiding obstacle and it's food
                self.set_rotation(0)
                return 2
            else: self.set_rotation(np.random.choice([-1, 1]))
        else:
            inputs = self.get_inputs()
            rot_speed = inputs @ self.weights
            self.set_rotation(np.clip(rot_speed, -1, 1))
        return -1

    def nb_inputs(self):
        return (1  # bias
                + self.nb_sensors * 3  # cam inputs
                #+ 2  # landmark inputs
                )
    
    def get_inputs(self):
        dists = self.get_all_distances()
        is_robots = self.get_all_robot_ids() != -1
        is_walls = self.get_all_walls()
        is_objects = self.get_all_objects() != -1

        robots_dist = np.where(is_robots, dists, 1)
        walls_dist = np.where(is_walls, dists, 1)
        objects_dist = np.where(is_objects, dists, 1)

        inputs = np.concatenate([[0], robots_dist, walls_dist, objects_dist])
        assert(len(inputs) == self.nb_inputs())
        return inputs

    def broadcast(self):
        for robot_controller in self.get_all_robot_controllers():
            if robot_controller:
                if not robot_controller.deactivated:
                    robot_controller.exchange(self.id, self)
                    self.exchange(robot_controller.id, robot_controller)

    def exchange(self,robID, robot):
        self.gList[robID] = robot
        robot.gList[self.id] = self

    def inZone(self):
        x, y = self.absolute_position
        if x >= self.dropZoneX and y >= self.dropZoneY:
            return True
        else: return False

    def new_generation(self):
        if self.gList:
            randKey = np.random.choice(list(self.gList.keys()))
            selected = self.gList[randKey]
            self.variation(selected)
            self.gList.clear()
            self.next_gen_in_it = self.next_gen_every_it
        else:
            self.deactivated = True

    def euclidean(self, coord1, coord2):
        x = (coord1[0]-coord2[0])**2
        y = (coord1[1]-coord2[1])**2
        return np.sqrt(x+y)
   
    def variation(self, other):
        parent2 = other.genome.copy()
        parent1 = self.genome
        for i in range(3): parent2[i] += parent1[i]
        v1 = [x%256 for x in parent2]
        v2 = [x//2 for x in parent2]
        mutate = [None]*3
        for i in range(3):
            mutate[i] = (v1[i] + v2[i])//2
        self.genome = mutate
        self.set_color(*self.genome)
        new_weights = other.weights.copy()
        self.weights = np.random.normal(new_weights, 0.1   )
    
    def inspect(self, prefix=""):
        output = "received weights from: \n"
        output += str(list(self.gList.keys()))
        return output
        