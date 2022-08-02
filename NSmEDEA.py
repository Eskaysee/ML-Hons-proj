from pyroborobo import Pyroborobo, Controller, MovableObject
import numpy as np

class MedeaController(Controller):

    def __init__(self, wm):
        super().__init__(wm)
        self.gList = dict()
        self.rob = Pyroborobo.get()
        self.next_gen_every_it = 400
        self.deactivated = False
        self.next_gen_in_it = self.next_gen_every_it
        self.genome = []
        self.seek = True
        self.dropZoneX, self.dropZoneY = np.array(self.rob.arena_size) *0.7
        self.foods = set()
        self.novelty = 0

    def reset(self):
        if self.genome == []:
            initCol = np.random.randint(9) % 3
            if initCol == 0: self.genome = [255,0,0]
            elif initCol == 1: self.genome = [0,255,0]
            elif initCol == 2: self.genome = [0,0,255]
            self.set_color(*self.genome)

    def step(self):
        self.next_gen_in_it -= 1
        if self.next_gen_in_it <= 0 or self.deactivated:
            self.novelty = self.nSearch(2)
            self.new_generation()
            self.next_gen_in_it = self.next_gen_every_it

        if self.deactivated:
            self.set_color(0, 0, 0)
            self.set_translation(0)
            self.set_rotation(0)
        else:
            # Movement
            self.set_translation(1)
            if (self.seek == True):
                cam = self.find()
                if cam>-1:
                    obj = self.get_object_instance_at(cam)
                    self.foods.add(obj)
                    #print("obj orientation is", self.get_robot_relative_orientation_at(cam))
                    #print("my orientation is", self.absolute_orientation)        
            else:
                self.seek = self.drop()
            # Share weights
            self.broadcast()
            self.novelty = self.nSearch(2)

    def drop(self):
        orient = self.get_closest_landmark_orientation()
        myOrient = self.absolute_orientation
        self.set_translation(1)
        #print("ORIENT:", orient, "my orient:", self.absolute_orientation)
        if myOrient > orient:
            self.set_rotation(myOrient-0.0125)
        else:
            self.set_rotation(myOrient+0.0125)
        #self.set_rotation(orient)
        if self.inZone():
            #print("dropped")
            return True

    def isTaken(self, sensr):
        obj = self.get_object_instance_at(sensr)
        return obj.taken(self.get_id())

    def find(self):
        camera_dist = self.get_all_distances()
        left = False; right = False
        if camera_dist[1] < 1:  # if we see something on our left
            if self.get_object_at(1) != -1 and not self.inZone() and not self.isTaken(1):  # And it is food
                self.set_rotation(-0.5)  # turn left
                return 1
            else: left = True
        elif camera_dist[3] < 1:  # Otherwise, if we see something on our right
            if self.get_object_at(3) != -1 and not self.inZone() and not self.isTaken(3):
                self.set_rotation(0.5)  # turn right
                return 3
            else: right = True
        if camera_dist[2] < 1:  # if we see something in front of us
            if self.get_object_at(2) != -1 and not self.inZone() and not self.isTaken(2):  # If we are not avoiding obstacle and it's food
                self.set_rotation(0)
                return 2
            elif left:
                self.set_rotation(1)
            elif right:
                self.set_rotation(-1)
            else: self.set_rotation(np.random.choice([-1, 1]))
        elif left:
            self.set_rotation(np.random.choice([0, 0.5]))
        elif right:
            self.set_rotation(np.random.choice([0, -0.5]))
        else: self.set_rotation(np.random.choice([-0.5, 0, 0.5]))
        return -1

    def broadcast(self):
        for robot_controller in self.get_all_robot_controllers():
            if robot_controller:
                robot_controller.exchange(self.id, self)
                #self.exchange(robot_controller.id, robot_controller)

    def exchange(self,robID, robot):
        self.gList[robID] = robot
        #robot.gList[self.id] = self

    def inZone(self):
        x, y = self.absolute_position
        if x > self.dropZoneX and y > self.dropZoneY:
            return True
        else: return False

    def new_generation(self):
        if self.gList:
            maxNovel = -1
            selected = None
            #print("my novelty is", self.novelty, "& food collected:", len(self.foods))
            for gene in self.gList:
                if (self.gList[gene].novelty > maxNovel):
                    selected = self.gList[gene]
            #print("MY Parents Are", self.id, "and", selected.id)
            #print("Dad:", "[",self.genome[0],",",self.genome[1],",",self.genome[2],"]")
            #print("Mom:", "[",selected.genome[0],",",selected.genome[1],",",selected.genome[2],"]")
            mutation = self.variation(self.genome, selected.genome.copy())
            #print("MY PHENOTYPE IS...", "[",mutation[0],",",mutation[1],",",mutation[2],"]\n")
            self.genome = mutation
            self.gList.clear()
            self.deactivated = False
            self.set_color(*self.genome)
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
    
    def variation(self, parent1, parent2):
        for i in range(3): parent2[i] += parent1[i]
        v1 = [x%256 for x in parent2]
        v2 = [x//2 for x in parent2]
        mutate = [None]*3
        for i in range(3):
            mutate[i] = (v1[i] + v2[i])//2
        return mutate
    
    def inspect(self, prefix=""):
        output = "received weights from: \n"
        output += str(list(self.gList.keys()))
        return output

##################################################################################

class Food(MovableObject):
    def __init__(self, id_, data):
        MovableObject.__init__(self, id_)  # Do not forget to call super constructor
        self.stored = False
        #self.taken = False
        self.rob = Pyroborobo.get()
        self.dropZoneX, self.dropZoneY = np.array(self.rob.arena_size) *0.65
        self.robID = -1
        '''self.data = data
        self.expiry = 250
        self.lifetime = 0
        self.newHarvest = 100
        self.wait = 0
        self.expired = False

    def reset(self):
        self.expired = False
        self.register()
        self.show()
        self.wait = 0
        self.lifetime = 0'''

    def step(self):
        super().step()
        x, y = self.position
        if x > self.dropZoneX and y > self.dropZoneY:
            self.set_color(0,0,0)
            self.stored = True
            self.robID = -2

    def taken(self, rob_id):
        if self.robID == -1: return False
        elif self.robID != rob_id: return True
        else: return False

    def is_pushed(self, rob_id, speed):
        #if self.stored: return
        super().is_pushed(rob_id, speed)
        if rob_id >= self.rob.robot_index_offset:
            robot = self.rob.controllers[rob_id-self.rob.robot_index_offset]
            if self.robID == -1:
                self.robID = robot.get_id()
            #if robot.seek: robot.seek = False
        #print(rob_id, speed[0], speed[1])

    def inspect(self, prefix=""):
        return f"""I'm a Food with id: {self.id}"""

def main():
    rob = Pyroborobo.create("config/NSmEDEA.properties",
                            controller_class=MedeaController,
                            object_class_dict={'_default': Food})
    rob.start()
    rob.update(10000)
    rob.close()


if __name__ == "__main__":
    main()
