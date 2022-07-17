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
            self.new_generation()
            self.next_gen_in_it = self.next_gen_every_it

        if self.deactivated:
            self.set_color(0, 0, 0)
            self.set_translation(0)
            self.set_rotation(0)
        else:
            # Movement
            self.set_translation(1)
            if self.get_wall_at(2):  # or in front of us
                self.set_rotation(np.random.choice([-0.5, 0.5]))
            elif self.get_object_at(1) != -1:
                self.set_rotation(-0.5)
            elif self.get_object_at(3) != -1:
                self.set_rotation(0.5)
            else:
                self.set_rotation(np.random.choice([0, -0.5, 0.5]))
            # Share weights
            self.broadcast()
            if self.get_distance_at(2) < 0.6:
                if self.get_robot_id_at(1) != -1:
                    self.set_rotation(0.5)
                elif self.get_robot_id_at(3) != -1:
                    self.set_rotation(-0.5)

    def broadcast(self):
        for robot_controller in self.get_all_robot_controllers():
            if robot_controller:
                robot_controller.exchange(self.id, self)
                #self.exchange(robot_controller.id, robot_controller)

    def exchange(self,robID, robot):
        self.gList[robID] = robot
        #robot.gList[self.id] = self

    def new_generation(self):
        if self.gList:
            selected = self.novelty(self.gList);
            print("MY Parents Are", self.id, "and", selected.id)
            print("Dad:", "[",self.genome[0],",",self.genome[1],",",self.genome[2],"]")
            print("Mom:", "[",selected.genome[0],",",selected.genome[1],",",selected.genome[2],"]")
            mutation = self.variation(self.genome, selected.genome.copy())
            print("MY PHENOTYPE IS...", "[",mutation[0],",",mutation[1],",",mutation[2],"]\n")
            self.genome = mutation
            self.gList.clear()
            self.deactivated = False
            self.set_color(*self.genome)
        else:
            self.deactivated = True

    def novelty(self, glist):
        maxKey = 0
        maxNovel = -1
        for genome in glist:
            metric = self.euclidean(self.absolute_position, glist[genome].absolute_position)
            #metric = self.mates(glist[genome].gList)
            if (metric > maxNovel): 
                maxNovel = metric
                maxKey = genome
        return glist[maxKey]
    
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

#########################################

class Food(MovableObject):
    def __init__(self, id_, data):
        MovableObject.__init__(self, id_)  # Do not forget to call super constructor
        self.data = data
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
        self.lifetime = 0

    def step(self):
        super().step()
        #if self.expired:
        #    self.wait -= 1
        #    self.hide()
        #    self.unregister()
        #    if self.wait <= 0:
        #        self.lifetime = 0
        #        self.expired = False
        #else:
        #    self.register()
        #    self.show()
        #    if self.lifetime >= self.expiry:
        #        self.wait = self.newHarvest
        #        self.expired = True

    def is_pushed(self, rob_id, speed):
        super().is_pushed(rob_id, speed)
        #self.lifetime+=1
        #print(f"I'm moved by {rob_id-1048576}")

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
