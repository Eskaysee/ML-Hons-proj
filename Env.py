from pyroborobo import Pyroborobo, WorldObserver, MovableObject
import time, sys
import numpy as np
import NSmEDEA, FitmEDEA, RandmEDEA

class Food(MovableObject):
    def __init__(self, id_, data=None):
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
        if self.robID == -2: return True
        if self.type == 1:
            if self.robID == -1: return False
            elif self.robID != rob_id: return True
        elif self.type == 2:
            if len(self.robs) < 2: return False
            else: return True
        elif self.type == 3:
            if len(self.robs) < 3: return False
            else: return True
        return False

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
        if self.robID == -2:
            return f"\nResource: {id} \nType: {rType} \nStored: True \nRobots: {robs} \n"
        else: return f"\nResource: {id} \nType: {rType} \nStored: False\n"

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
            #if self.robID == -2: return
        super().is_pushed(rob_id, speed)

    def inspect(self, prefix=""):
        return f"""I am {self.get_id()} with {len(self.robs)} pushing me: {str(self.robs)}""" #f"""I'm a Food with id: {self.id}"""

##########################################################################################
        
class MWO(WorldObserver):
    def __init__(self, world):
        super().__init__(world)
        self.rob = Pyroborobo.get()
        self.timeStart = None
        self.timeStop = None
        self.halfGenT = None
        self.fullGenT = None
        self.stored = 0
        self.generation = 0
        self.C = []
        self.f3 = None
        self.halfgenstock = 0
        self.check = True

    def init_pre(self):
        super().init_pre()
        self.timeStart = time.time()
        self.f3 = open("results/ExperimentsEnv2.txt", "r+")
        if self.f3.read(1) == "\n":
            exNum = int(self.f3.readlines()[-33][20:])
        else: exNum = 1
        self.C = [f"\nHybrid Experiment {exNum}"]
    
    def step_pre(self):
        super().step_pre()
        if self.halfgenstock!=0 and self.check:
            if self.stored<self.halfgenstock:
                storage = self.storedItems()
                self.stored = sum(list(storage.values())) - self.halfgenstock
            elif self.stored==self.halfgenstock:
                self.fullGenT = self.stopTimer(self.fullGenT)
                self.check = False
        if self.rob.iterations == 3001:
            self.timeStart = time.time()

    def step_post(self):
        super().step_post()
        if self.rob.iterations != 0 and self.rob.iterations%600 == 0:
            if self.rob.iterations == 3000:
                self.halfGenT = self.stopTimer(self.halfGenT)
                self.halfgenstock = sum(list(self.storedItems().values()))
            elif self.rob.iterations == 6000:
                self.fullGenT = self.stopTimer(self.fullGenT)
            self.generation += 1
            activeRobs = self.activeRobots();storedItems = self.storedItems()
            totRobs = len(self.rob.controllers); totObjs = len(self.rob.objects)
            self.C.append(f"\nAfter {self.generation} generation(s), there are {activeRobs} active robots out of {totRobs}. {totRobs - activeRobs} are dead.\n")
            self.C.append(f"There are {self.stored} stored resources, specifically {str(storedItems)}, out of {totObjs}. {totObjs - self.stored} not yet stored. \n")
        if self.rob.iterations == 6000: 
            self.C.append(f"Took {self.halfGenT} to store {self.halfgenstock} resources during the first 5 generations\n")
            self.C.append(f"Took {self.fullGenT} to store {self.stored} resources during the following 5 generations\n")
            self.C.append("\n################################################################################################\n")
            self.f3.writelines(self.C)
            self.f3.close()

    def stopTimer(self, genTimer):
        if genTimer is None:
            self.timeStop = time.time()
            genTimer = time.strftime("%M minute(s), %S seconds", time.gmtime(self.timeStop - self.timeStart))
        return genTimer
    
    def activeRobots(self):
        activeRobs = 0;#
        for robot in self.rob.controllers:
            if not robot.deactivated:
                activeRobs +=1
        return activeRobs

    def storedItems(self):
        storedItems = {"A":0, "B":0, "C":0};
        for item in self.rob.objects:
            if item.robID == -2:
                if item.type == 1:
                    storedItems["A"] += 1
                elif item.type == 2:
                    storedItems["B"] += 1
                elif item.type == 3:
                    storedItems["C"] += 1
        return storedItems

################################################################################################

def main(argv):
    input = str(argv); input = input.strip()
    f3 = open("results/ExperimentsEnv2.txt", "a")
    f3.close()
    if input == "random":
        rob = Pyroborobo.create("config/NSmEDEA.properties",
                            controller_class=RandmEDEA.MedeaController,
                            world_observer_class=MWO,
                            object_class_dict={'_default': Food})
    elif input == "fitness":
        rob = Pyroborobo.create("config/NSmEDEA.properties",
                            controller_class=FitmEDEA,
                            world_observer_class=MWO,
                            object_class_dict={'_default': Food})
    elif input == "hybrid":
        rob = Pyroborobo.create("config/NSmEDEA.properties",
                            controller_class=NSmEDEA.MedeaController,
                            world_observer_class=MWO,
                            object_class_dict={'_default': Food})
    else: sys.exit()
    rob.start()
    rob.update(3001)
    resIdx = 51
    for i in range(35):
        rob.add_object(Food(resIdx+i))
    rob.update(3001)

    robStatus = ""; resourceStatus = ""
    for robot in rob.controllers:
        robStatus += robot.eulogy()
    for item in rob.objects:
        resourceStatus += item.stored()
    f1 = open("results/HybridRobots", "w")
    f2 = open("results/HybridResources", "w")
    f1.write(robStatus)
    f2.write(resourceStatus)
    f1.close()
    f2.close()
    rob.close()


if __name__ == "__main__":
    main(sys.argv[1])
