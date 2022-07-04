from pyroborobo import Pyroborobo, Controller
import numpy as np

class MedeaController(Controller):


    def __init__(self, wm):
        super().__init__(wm)
        #self.weights = None
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
        if self.next_gen_in_it < 0 or self.deactivated:
            self.new_generation()
            self.next_gen_in_it = self.next_gen_every_it

        if self.deactivated:
            self.set_color(0, 0, 0)
            self.genome = []
            self.gList = dict()
            self.set_translation(0)
            self.set_rotation(0)
        else:
            #self.set_color(0, 0, 255)
            # Movement
            #inputs = self.get_inputs()
            #trans_speed, rot_speed = inputs @ self.weights
            self.set_translation(1)
            self.set_rotation(np.random.choice([0, -0.5, 0.5]))
            # Share weights
            self.broadcast()

    def nb_inputs(self):
        return (1  # bias
                + self.nb_sensors * 3  # cam inputs
                + 2  # landmark inputs
                )

    def broadcast(self):
        for robot_controller in self.get_all_robot_controllers():
            if robot_controller:
                robot_controller.exchange(self.id, self.genome)

    def exchange(self,robID, genes):
        self.gList[robID] = genes

    def get_inputs(self):
        dists = self.get_all_distances()
        is_robots = self.get_all_robot_ids() != -1
        is_walls = self.get_all_walls()
        is_objects = self.get_all_objects() != -1

        robots_dist = np.where(is_robots, dists, 1)
        walls_dist = np.where(is_walls, dists, 1)
        objects_dist = np.where(is_objects, dists, 1)

        landmark_dist = self.get_closest_landmark_dist()
        landmark_orient = self.get_closest_landmark_orientation()

        inputs = np.concatenate([[1], robots_dist, walls_dist, objects_dist, [landmark_dist, landmark_orient]])
        #assert(len(inputs) == self.nb_inputs())
        return inputs

    def new_generation(self):
        if self.gList:
            randomRob = np.random.choice(list(self.gList.keys()))
            selection  = self.gList[randomRob]
            #new_weights = self.received_weights[new_weights_key]
            # mutation 1
            #selection[randomRob%3] += 32;
            #variation = [x%256 for x in selection]
            # mutation 2
            variation = np.random.normal(selection, 0.5)
            variation = [abs(int(x)) for x in variation]
            #print("NEW COLOUR IS...", "[",variation[0],",",variation[1],",",variation[2],"]")
            self.genome = variation
            self.gList.clear()
            self.deactivated = False
            self.set_color(*self.genome)
        else:
            self.deactivated = True

    def inspect(self, prefix=""):
        output = "inputs: \n" + str(self.get_inputs()) + "\n\n"
        output += "received weights from: \n"
        output += str(list(self.gList.keys()))
        return output

def main():
    rob = Pyroborobo.create("config/talking_robots.properties",
                            controller_class=MedeaController,
                            object_class_dict={'_default': ResourceObject, 'select': SelectObject})
    rob.start()
    rob.update(10000)
    rob.close()


if __name__ == "__main__":
    main()
