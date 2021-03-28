from copy import deepcopy
from enum import Enum
from typing import List
import random
import json
import sys

HEALTH = "HEALTH"
POSITION = "POSITION"
MMSTATE = "MMSTATE"
ARROWS = "ARROWS"
ACTIONS = "ACTIONS"
MATERIALS = "MATERIALS"


class Health(Enum):
    H_0, H_25, H_50, H_75, H_100 = range(5)


class Materials(Enum):
    M_0, M_1, M_2 = range(3)


class Positions(Enum):
    W, N, E, S, C = range(5)


class MMState(Enum):
    D, R = range(2)


class Arrows(Enum):
    A_0, A_1, A_2, A_3 = range(4)


debug = False
if len(sys.argv) == 2 and sys.argv[1] == "d":
    debug = True

X = 22
arr = [1 / 2, 1, 2]
Y = arr[X % 3]
STEP_COST = -10 / Y
GAMMA = 0.999
ERROR = 0.001


class Actions(Enum):
    UP, LEFT, DOWN, RIGHT, STAY, SHOOT, HIT, CRAFT, GATHER, NONE = range(10)


class State:
    def __init__(self, value, health, arrows, materials, mm_state, position):
        self.value: float = value
        self.actions: List[Actions] = []
        self.health: Health = Health(health)
        self.arrows: Arrows = Arrows(arrows)
        self.materials: Materials = Materials(materials)
        self.mm_state: MMState = MMState(mm_state)
        self.pos: Positions = Positions(position)
        self.favoured_action: Actions = Actions.NONE

    def __str__(self):
        # return f"Pos: {self.pos.name}  Mat: {self.materials.value} Arrow: {self.arrows.value} MM: {self.mm_state.name} MM_health: {self.health.value} Value = " + "{:0.2f}".format(
        #     self.value)
        return f"({self.pos.name},{self.materials.value},{self.arrows.value},{self.mm_state.name},{self.health.value * 25})"

    def get_info(self):
        return {
            POSITION: self.pos,
            MATERIALS: self.materials,
            ARROWS: self.arrows,
            MMSTATE: self.mm_state,
            HEALTH: self.health,
        }

    def filter(self):
        self.actions = [action for action in self.actions if self.filter_action(action)]

    def filter_action(self, action: Actions):
        if action == Actions.SHOOT:
            return self.arrows.value > 0
        elif action == Actions.CRAFT:
            return self.arrows != Arrows.A_3 and self.materials.value > 0
        elif action == Actions.GATHER:
            return self.materials != Materials.M_2
        elif action == Actions.NONE:
            return self.health == Health.H_0
        else:
            return True


class ValueIteration:
    def __init__(self):
        self.states: [State] = []
        self.discount_factor: float = GAMMA
        self.iteration: int = -1

    def iterate(self):
        self.iteration += 1
        print(f"iteration={self.iteration}")
        new_states = []
        for state in deepcopy(self.states):
            if debug:
                print("Deciding optimal action for", str(state))
            action_values = [self.action_value(action, state)[0] for action in state.actions]
            state.value = max(action_values)
            state.favoured_action = state.actions[action_values.index(state.value)]
            print(str(state) + ":" + state.favoured_action.name +
                  "=[{:0.3f}]".format(state.value),
                  end="\n")
            new_states.append(state)
        stop = True
        max_diff = 0
        for idx in range(len(new_states)):
            diff = self.states[idx].value - new_states[idx].value
            if abs(diff) > ERROR:
                stop = False
            max_diff = max(max_diff, abs(diff))
        print(max_diff, file=sys.stderr)
        self.states = new_states
        if stop:
            return -1
        return 0

    def action_value(self, action: Actions, state: State):
        results = []
        if debug:
            print(action.name)
        # result[0] is unsuccessful state, result[1:] are successful
        new_state_info = state.get_info()
        if action == Actions.NONE:
            return state.value, []
        if state.pos == Positions.C:
            if action == Actions.UP:
                # unsuccessful
                new_state_info[POSITION] = Positions.E
                results.append((0.15, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.N
                results.append((0.85, deepcopy(new_state_info)))
            elif action == Actions.DOWN:
                # unsuccessful
                new_state_info[POSITION] = Positions.E
                results.append((0.15, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.S
                results.append((0.85, deepcopy(new_state_info)))
            elif action == Actions.LEFT:
                # unsuccessful
                new_state_info[POSITION] = Positions.E
                results.append((0.15, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.W
                results.append((0.85, deepcopy(new_state_info)))
            elif action == Actions.RIGHT:
                # unsuccessful
                new_state_info[POSITION] = Positions.E
                results.append((1.0, deepcopy(new_state_info)))
                # successful
                # new_state_info[POSITION] = Positions.E
                # results.append((0.85, deepcopy(new_state_info)))
            elif action == Actions.STAY:
                # unsuccessful
                new_state_info[POSITION] = Positions.E
                results.append((0.15, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.C
                results.append((0.85, deepcopy(new_state_info)))
            elif action == Actions.SHOOT:
                if state.get_info()[ARROWS].value > 0:
                    # # unsuccessful
                    new_state_info[ARROWS] = Arrows(new_state_info[ARROWS].value - 1)
                    results.append((0.5, deepcopy(new_state_info)))
                    # successful
                    new_state_info[HEALTH] = Health(max(0, new_state_info[HEALTH].value - 1))
                    results.append((0.5, deepcopy(new_state_info)))
                else:
                    # unsuccessful
                    results.append((1, deepcopy(new_state_info)))
            elif action == Actions.HIT:
                # # unsuccessful
                # results.append((0.9, deepcopy(new_state_info)))
                # successful
                new_state_info[HEALTH] = Health(max(0, new_state_info[HEALTH].value - 2))
                results.append((0.1, deepcopy(new_state_info)))

        elif state.pos == Positions.N:
            if action == Actions.DOWN:
                # unsuccessful
                new_state_info[POSITION] = Positions.E
                results.append((0.15, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.C
                results.append((0.85, deepcopy(new_state_info)))
            elif action == Actions.STAY:
                # unsuccessful
                new_state_info[POSITION] = Positions.E
                results.append((0.15, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.N
                results.append((0.85, deepcopy(new_state_info)))

            elif action == Actions.CRAFT:
                if new_state_info[MATERIALS].value > 0:
                    # unsuccessful
                    # results.append((0, deepcopy(new_state_info)))
                    # successful
                    new_state_info[ARROWS] = Arrows(min(new_state_info[ARROWS].value + 1, len(Arrows) - 1))
                    results.append((0.5, deepcopy(new_state_info)))
                    new_state_info = state.get_info()
                    new_state_info[ARROWS] = Arrows(min(new_state_info[ARROWS].value + 2, len(Arrows) - 1))
                    results.append((0.35, deepcopy(new_state_info)))
                    new_state_info = state.get_info()
                    new_state_info[ARROWS] = Arrows(min(new_state_info[ARROWS].value + 3, len(Arrows) - 1))
                    results.append((0.15, deepcopy(new_state_info)))
                else:
                    # unsuccessful
                    results.append((1.0, deepcopy(new_state_info)))

        elif state.pos == Positions.S:
            if action == Actions.UP:
                # unsuccessful
                new_state_info[POSITION] = Positions.E
                results.append((0.15, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.C
                results.append((0.85, deepcopy(new_state_info)))
            elif action == Actions.STAY:
                # unsuccessful
                new_state_info[POSITION] = Positions.E
                results.append((0.15, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.S
                results.append((0.85, deepcopy(new_state_info)))
            elif action == Actions.GATHER:
                # this might be wrong
                # unsuccessful
                # results.append((0.25, deepcopy(new_state_info)))
                # successful
                new_state_info[MATERIALS] = Materials(min(new_state_info[MATERIALS].value + 1, len(Materials) - 1))
                results.append((0.75, deepcopy(new_state_info)))

        elif state.pos == Positions.E:

            if action == Actions.LEFT:
                # unsuccessful
                # results.append((0.0, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.C
                results.append((1.0, deepcopy(new_state_info)))
            elif action == Actions.STAY:
                # unsuccessful
                # results.append((0.0, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.E
                results.append((1.0, deepcopy(new_state_info)))
            elif action == Actions.SHOOT:
                results = []
                if state.get_info()[ARROWS].value > 0:
                    new_state_info[ARROWS] = Arrows(new_state_info[ARROWS].value - 1)
                    results.append((0.1, deepcopy(new_state_info)))
                    # successful
                    new_state_info[HEALTH] = Health(max(0, new_state_info[HEALTH].value - 1))
                    results.append((0.9, deepcopy(new_state_info)))
                else:
                    results.append((1.0, deepcopy(new_state_info)))

            elif action == Actions.HIT:
                # unsuccessful
                # results.append((0.8, deepcopy(new_state_info)))  # miss with high prob
                # successful
                new_state_info[HEALTH] = Health(max(0, new_state_info[HEALTH].value - 2))
                results.append((0.2, deepcopy(new_state_info)))  # hit

        elif state.pos == Positions.W:
            if action == Actions.RIGHT:
                # unsuccessful
                # results.append((0.0, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.C
                results.append((1.0, deepcopy(new_state_info)))
            elif action == Actions.STAY:
                # unsuccessful
                # results.append((0.0, deepcopy(new_state_info)))
                # successful
                new_state_info[POSITION] = Positions.W
                results.append((1.0, deepcopy(new_state_info)))
            elif action == Actions.SHOOT:
                results = []
                if state.get_info()[ARROWS].value > 0:
                    # unsuccessful
                    new_state_info[ARROWS] = Arrows(new_state_info[ARROWS].value - 1)
                    results.append((0.75, deepcopy(new_state_info)))
                    # successful
                    new_state_info[HEALTH] = Health(max(0, new_state_info[HEALTH].value - 1))
                    results.append((0.25, deepcopy(new_state_info)))
                else:
                    # unsuccessful
                    results.append((1.0, deepcopy(new_state_info)))

        final_results = []
        got_hit = -1
        if state.get_info()[MMSTATE] == MMState.D:
            for result in results:
                new_state = result[1]
                new_state[MMSTATE] = MMState.D
                final_results.append((0.8 * result[0], deepcopy(new_state)))
                new_state[MMSTATE] = MMState.R
                final_results.append((0.2 * result[0], deepcopy(new_state)))

        elif state.get_info()[MMSTATE] == MMState.R:
            for result in results:
                final_results.append((0.5 * result[0], result[1]))  # MM just remains ready
            if state.get_info()[POSITION] == Positions.C or state.get_info()[POSITION] == Positions.E:

                new_state = deepcopy(state.get_info())  # get the new state for unsuccessful action
                new_state[MMSTATE] = MMState.D  # new MM state is dormant
                new_state[ARROWS] = Arrows.A_0  # new Arrow state is 0
                new_state[HEALTH] = Health(
                    min(new_state[HEALTH].value + 1, len(Health) - 1))  # new health state is + 25
                got_hit = len(final_results)  # index of action where you got hit
                final_results.append((0.5, deepcopy(new_state)))  # this new state has 0.5 probability
            else:
                for result in results:
                    result_state = deepcopy(result[1])
                    result_state[MMSTATE] = MMState.D
                    final_results.append((0.5 * result[0], deepcopy(result_state)))

        value: float = 0
        total_prob: float = 0.0
        for result in final_results:
            total_prob += result[0]
        # print(total)

        for idx, result in enumerate(final_results):
            reward = 0
            if got_hit == idx:
                reward = -40
            # print("value is " + str(self.getvalue(result[1])))
            STEP = STEP_COST
            # for the other task
            # if action == Actions.STAY:
            # print(result[1])
            if result[1][HEALTH].value == 0:
                reward = 50
            #     STEP = 0
            if debug:
                print("{:0.3f}".format(
                    result[0]) + f", state={self.getState(result[1])} value={self.getState(result[1]).value}")
            value += result[0] * (STEP + reward + GAMMA * self.getState(result[1]).value)
        if debug:
            print(value)

        for prob, res in final_results:
            assert (res != state.get_info())
        return value, final_results

    @classmethod
    def getIdx(cls, info):
        idx = info[POSITION].value * (len(Materials) * len(Arrows) * len(MMState) * len(Health)) + info[
            MATERIALS].value * (len(Arrows) * len(MMState) * len(Health)) + info[ARROWS].value * len(MMState) * len(
            Health) + info[MMSTATE].value * len(Health) + info[HEALTH].value
        return idx

    def getState(self, info) -> State:
        # print(result)
        idx = self.getIdx(info)
        assert (self.states[idx].get_info() == info)
        return self.states[idx]

    def train(self, max_iter):
        while self.iterate() != -1 and self.iteration < max_iter - 1:
            pass
        print(f"iteration={self.iteration}", file=sys.stderr)
        self.dump_states()

    def dump_states(self):
        with open("trained_states.txt", "w") as f:
            sts = []
            for idx, state in enumerate(self.states):
                sts.append({"id": idx, "action": state.favoured_action.value, "value": state.value})
            json.dump(sts, f)

    def load_states(self):
        with open("trained_states.txt", "r") as f:
            sts = json.load(f)
            for a_state in sts:
                ste = self.states[a_state["id"]]
                ste.value = a_state["value"]
                ste.favoured_action = Actions(a_state["action"])

    def __str__(self):
        s = ""
        for ste in self.states:
            s += str(ste)
        return s


vi = ValueIteration()
states_init = []
for pos in range(len(Positions)):
    for mat in range(len(Materials)):
        for arrow in range(len(Arrows)):
            for mmst in range(len(MMState)):
                for health in range(len(Health)):
                    state_1 = State(0, health, arrow, mat, mmst, pos)
                    # state_1.actions.append(Actions.STAY)
                    if state_1.pos == Positions.C:
                        state_1.actions.append(Actions.DOWN)
                        state_1.actions.append(Actions.UP)
                        state_1.actions.append(Actions.LEFT)
                        state_1.actions.append(Actions.RIGHT)
                        state_1.actions.append(Actions.HIT)
                        state_1.actions.append(Actions.SHOOT)
                    if state_1.pos == Positions.N:
                        state_1.actions.append(Actions.DOWN)
                        state_1.actions.append(Actions.CRAFT)
                    if state_1.pos == Positions.S:
                        state_1.actions.append(Actions.UP)
                        state_1.actions.append(Actions.GATHER)
                    if state_1.pos == Positions.E:
                        state_1.actions.append(Actions.LEFT)
                        state_1.actions.append(Actions.SHOOT)
                        state_1.actions.append(Actions.HIT)
                    if state_1.pos == Positions.W:
                        state_1.actions.append(Actions.RIGHT)
                        state_1.actions.append(Actions.SHOOT)
                    if state_1.health.value == 0:
                        state_1.actions = [Actions.NONE]
                        state_1.value = 0
                    state_1.filter()
                    states_init.append(state_1)

vi.states = states_init

vi.train(10)
# vi.load_states()

# total: List[float] = [0, 0, 0, 0, 0]
# for st in vi.states:
#     total[st.pos.value] += st.value
#
# print("Total values by position")
# for i in range(len(Positions)):
#     print(Positions(i))
# print(total)
#
# initial_state = State(value=0, position=Positions.W.value, materials=0, arrows=0, mm_state=MMState.D.value,
#                       health=Health.H_100.value)
# # initial_state = State(value=0, position=Positions.C.value, materials=2, arrows=0, mm_state=MMState.R.value,
# #                       health=Health.H_100.value)
# vi.simulate(initial_state)
