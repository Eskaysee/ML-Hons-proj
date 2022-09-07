from pyroborobo import Pyroborobo, Controller, MovableObject
import numpy as np

class MedeaController(Controller):

    def __init__(self, wm):
        super().__init__(wm)
        self.gList = dict()
        self.rob = Pyroborobo.get()
        self.next_gen_every_it = 600
        self.wait = 150
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
        #self.help = False
        self.novelty = 0
        self.skipSteps = 5

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
        
        elif self.next_gen_in_it <= 5:
            self.novelty = self.nSearch(3)
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
                #if self.inZone(): self.leave()
                self.find() #cam = self.find()
                #if self.inZone(): self.leave()       
            else:
                self.seek = self.drop()
                if self.wait <=0 :
                    self.avoid = True
                    #self.help =  False
                    self.wait = 100
            # Share weights
            self.broadcast()
            self.novelty = self.nSearch(3)

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
            comrades = []
            self.skipSteps -= 1
            if self.lastX == self.absolute_position[0] and self.lastY == self.absolute_position[1]:
                self.wait -=1
            else: 
                self.wait = 150
            
            if self.lastObj.type >= 2:
                comrades = list(self.lastObj.robs)
                comrades.remove(self.get_id())
            comrades.append(-1)
            if self.lastObj.type ==1:
                if (self.get_object_at(1)-1 != objID and self.get_object_at(1) != -1) or self.get_robot_id_at(0) not in comrades or self.get_wall_at(0) or self.get_wall_at(1):
                    self.set_rotation(0.5)
                elif (self.get_object_at(3)-1 != objID and self.get_object_at(3) != -1) or self.get_robot_id_at(4) not in comrades or self.get_wall_at(4) or self.get_wall_at(3):
                    self.set_rotation(-0.5)
            if not self.navigate(objID): return True
            if self.skipSteps <= 0:
                self.lastX, self.lastY = self.absolute_position
                self.skipSteps = 5
            return False
        else: 
            self.foods.add(objID)
            print(self.lastObj.stored())
            return True

    def eulogy(self):
        id = str(self.get_id())
        foods = str(self.foods)
        suitors = str(self.gList)
        colour = str(self.genome)
        return f"""Robot: {id}\
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
            else:
                self.removeAnchor()
                return False
        elif orient <= -0.25:
            self.set_rotation(-0.125)
            if self.get_object_at(2)-1 == objID:
                self.set_rotation(0)
            elif self.get_object_at(3)-1 == objID:
                self.set_rotation(0.25)
            elif self.get_object_at(1)-1 == objID:
                self.set_rotation(-0.25)
            else:
                self.removeAnchor()
                return False
        else:
            self.set_rotation(orient)
            if self.get_object_at(3)-1 == objID:
                self.set_rotation(0.125)
            elif self.get_object_at(1)-1 == objID:
                self.set_rotation(-0.125)
        return True
            
    def isTaken(self, sensr):
        obj = self.get_object_instance_at(sensr)
        return obj.taken(self.get_id())

    def find(self):
        camera_dist = self.get_all_distances()
        left = False; right = False
        if camera_dist[1] < 1:  # if we see something on our left
            if (self.get_object_at(1) != -1 and not self.inZone() and not self.isTaken(1)):# or collab:  # And it is food
                self.set_rotation(-0.5)  # turn left
                return 1
            else: left = True
        elif camera_dist[3] < 1:  # Otherwise, if we see something on our right
            if (self.get_object_at(3) != -1 and not self.inZone() and not self.isTaken(3)):# or collab:
                self.set_rotation(0.5)  # turn right
                return 3
            else: right = True
        if camera_dist[2] < 1:  # if we see something in front of us
            #collab = False if self.get_robot_controller_at(2) is None else self.get_robot_controller_at(2).assist()
            if (self.get_object_at(2) != -1 and not self.inZone() and not self.isTaken(2)):# or collab:  # If we are not avoiding obstacle and it's food
                self.set_rotation(0)
                return 2
            elif left:
                self.set_rotation(1)
            elif right:
                self.set_rotation(-1)
        elif left:
            self.set_rotation(np.random.choice([0, 0.25]))
        elif right:
            self.set_rotation(np.random.choice([0, -0.25]))
        else:
            inputs = self.get_inputs()
            rot_speed = inputs @ self.weights
            #print("inputs:\n", str(inputs), '\n')
            #print("========================================")
            #print("weights:\n", str(self.weights), '\n')
            #print(str(self.genome))
            #print("ROTATION SPEEED:", rot_speed, '\n')
            #print(trans_speed, "AND", rot_speed)
            self.set_translation(1)
            self.set_rotation(np.clip(rot_speed, -1, 1))
        return -1

    def nb_inputs(self):
        return (1  # bias
                + self.nb_sensors * 3  # cam inputs
                + 2  # landmark inputs
                )
    
    def get_inputs(self):
        dists = self.get_all_distances()
        is_robots = self.get_all_robot_ids() != -1
        #print(str(is_robots))
        is_walls = self.get_all_walls()
        #print(str(is_walls))
        is_objects = self.get_all_objects() != -1
        #print(str(is_objects), '\n')

        robots_dist = np.where(is_robots, dists, 0)
        #print(str(robots_dist))
        walls_dist = np.where(is_walls, dists, 0)
        #print(str(walls_dist))
        objects_dist = np.where(is_objects, dists, 0)
        #print(str(objects_dist), '\n', "NEXT", '\n')

        landmark_dist = self.get_closest_landmark_dist()
        landmark_orient = self.get_closest_landmark_orientation()

        inputs = np.concatenate([[1], robots_dist, walls_dist, objects_dist, [landmark_dist, landmark_orient]])
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
        f1 = open("results/\'Dead Robots\'", "a")
        f1.writelines(self.eulogy())
        f1.close()
        if self.gList:
            maxNovel = -1
            selected = None
            birth = "I am robot " + str(self.get_id()) + " and I have " + str(len(self.gList)) + " suitors."
            birth += "\nThey are: " + str(list(self.gList.keys()))
            for gene in self.gList:
                if (self.gList[gene].novelty > maxNovel):
                    selected = self.gList[gene]
            birth += "\nMy dad: "+ str(self.genome)+ ", My mom: " + str(selected.genome)
            self.variation(selected)
            birth += "\nOffspring" + str(self.genome) + '\n'
            self.gList.clear()
            #self.deactivated = False
            self.next_gen_in_it = self.next_gen_every_it
            f2 = open("results/\'Birthed Robots\'", "a")
            f2.writelines(birth)
            f2.close()
        else:
            self.deactivated = True

    def nSearch(self, space):
        k = space
        distances = []
        for genome in self.gList:
            distances.append(self.euclidean(self.absolute_position, self.gList[genome].absolute_position))
            #metric = self.mates(glist[genome].gList)
            if (len(distances) == k): break
        return sum(distances)/k
    
    def euclidean(self, coord1, coord2):
        x = (coord1[0]-coord2[0])**2
        y = (coord1[1]-coord2[1])**2
        return np.sqrt(x+y)

    def mates(self, partners):
        return len(partners)
    
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
        self.weights = other.weights.copy()
        #print(str(self.weights), '\n')
    
    def inspect(self, prefix=""):
        output = "received weights from: \n"
        output += str(list(self.gList.keys()))
        return output

##################################################################################

class Food(MovableObject):
    def __init__(self, id_, data):
        MovableObject.__init__(self, id_)  # Do not forget to call super constructor
        self.rob = Pyroborobo.get()
        self.dropZoneX, self.dropZoneY = np.array(self.rob.arena_size) *0.65
        while self.position[0] > self.dropZoneX and self.position[1] > self.dropZoneY:
            self.relocate() 
        self.robID = -1
        self.type = -1
        self.robs = set()
        self.unregister()
        if self.type == -1:
            self.type = np.random.randint(1,5)%3
            if self.type == 0: self.type = 3
        if self.type == 2:
            self.radius = 10
            self.set_footprint_radius(12)
            self.set_color(0,0,255)
        elif self.type == 3:
            self.radius = 15
            self.set_footprint_radius(18)
            self.set_color(255,0,0)
        self.register()
    
    def step(self):
        super().step()
        if self.inZone():
            self.set_color(0,0,0)
            self.robID = -2

    def inZone(self):
        x, y = self.position
        if x > self.dropZoneX and y > self.dropZoneY:
            return True
        else: return False

    def taken(self, rob_id):
        if self.type == 1:
            if self.robID == -1: return False
            elif self.robID != rob_id: return True
        elif self.type == 2:
            if len(self.robs) < 2: return False
            else: return True
        elif self.type == 3:
            if len(self.robs) < 3: return False
            else: return True
        else: return False

    def removeAnchor(self, rID):
        if len(self.robs) == 1:
            self.robID = -1
        lst = list(self.robs)
        lst.remove(rID)
        self.robs = set(lst)

    def stored(self):
        id = str(self.get_id())
        if self.type == 1: rType = "A"
        elif self.type == 2: rType = "B"
        else: rType = "C"
        robs = str(self.robs)
        return f"Resource {id} of type: {rType} has been stored by robots {robs} \n"

    def is_pushed(self, rob_id, speed):
        if rob_id >= self.rob.robot_index_offset:
            robot = self.rob.controllers[rob_id-self.rob.robot_index_offset]
            if self.robID == -1:
                if robot.seek:
                    self.robID = robot.get_id()
                    robot.lastObj = self
                    robot.seek = False
                    #robot.foods.add(self.get_id())
                    self.robs.add(robot.get_id())
            if self.type == 2:
                if len(self.robs) < 2:
                    if robot.seek: 
                        robot.lastObj = self
                        robot.seek = False
                        #robot.foods.add(self.get_id())
                        self.robs.add(robot.get_id())
                    return
            elif self.type == 3:
                if len(self.robs) < 3: 
                    if robot.seek:
                        robot.lastObj = self
                        robot.seek = False
                        #robot.foods.add(self.get_id())
                        self.robs.add(robot.get_id())
                    return
        super().is_pushed(rob_id, speed)

    def inspect(self, prefix=""):
        return f"""I am {self.get_id()} with {len(self.robs)} pushing me: {str(self.robs)}""" #f"""I'm a Food with id: {self.id}"""

def main():
    rob = Pyroborobo.create("config/NSmEDEA.properties",
                            controller_class=MedeaController,
                            object_class_dict={'_default': Food})
    f1 = open("results/\'Dead Robots\'", "w+")
    f2 = open("results/\'Birthed Robots\'", "w+")
    f3 = open("results/\'Stored Items\'", "w+")
    rob.start()
    rob.update(10000)
    rob.close()
    f1.close()
    f2.close()
    f3.close()


if __name__ == "__main__":
    main()
