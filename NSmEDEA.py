from pyroborobo import Pyroborobo, Controller
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
            print("[",self.genome[0],",",self.genome[1],",",self.genome[2],"]")
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
            self.set_rotation(np.random.choice([0, -0.5, 0.5]))
            # Share weights
            self.broadcast()

    def broadcast(self):
        for robot_controller in self.get_all_robot_controllers():
            if robot_controller:
                robot_controller.exchange(self.id, self.genome)

    def exchange(self,robID, genes):
        self.gList[robID] = genes.copy()

    def new_generation(self):
        if self.gList:
            randomRob = np.random.choice(list(self.gList.keys()))
            selection  = self.gList[randomRob]
            print("MY Parents Are", self.id, "and", randomRob)
            print("Dad:", "[",self.genome[0],",",self.genome[1],",",self.genome[2],"]")
            print("Mom:", "[",selection[0],",",selection[1],",",selection[2],"]")
            # mutation 3
            #variation = np.random.normal(selection, 0.5)
            #variation = [abs(int(x)) for x in variation]
            mutation = self.variation(self.genome, selection.copy())
            print("MY PHENOTYPE IS...", "[",mutation[0],",",mutation[1],",",mutation[2],"]\n")
            self.genome = mutation
            self.gList.clear()
            self.deactivated = False
            self.set_color(*self.genome)
        else:
            self.deactivated = True

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

def main():
    rob = Pyroborobo.create("config/NSmEDEA.properties",
                            controller_class=MedeaController)
    rob.start()
    rob.update(10000)
    rob.close()


if __name__ == "__main__":
    main()
