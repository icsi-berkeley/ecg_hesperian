"""

Author: vivekraghuram <vivek.raghuram@berkeley.edu>

A HesperianProblemSolver that extends the CoreProblemSolver in the NLUAS module.

Actions, like "move", should be named by predicate + action type.
Thus: query_move, command_move, etc.
Or: query_be, command_be, etc.

"""

from nluas.app.core_solver import *
from nluas.utils import *
import sys
from threading import Thread, Lock
from functools import wraps
from nluas.Transport import Transport
import json
import time

class BasicHesperianProblemSolver(CoreProblemSolver):
    def __init__(self, args):
        CoreProblemSolver.__init__(self, args)
        self._recent = None
        self._wh = None
        self._terminate = False


    def send_and_receive(self, message, timeout=5):
        """
        Sends message to the adapter and waits for a response
        """
        send_time = time.time()
        self._response = None
        self.transport.send(self.adapter_address, json.dumps(message))
        print("sent: ", message)

        while time.time() - send_time <= timeout:
            if self._response:
                print("received: ", self._response)
                if self._response["status"] == "success" or 'remaining' in self._response:
                    return self._response
                raise RuntimeWarning("Could not complete: " + str(message))
        raise RuntimeError("Command timed out: " + str(message))

    def solve_serial(self, parameters, predicate):
        """
        Solves a serial event
        """
        self.route_action(parameters['process1'], predicate)
        self.route_action(parameters['process2'], predicate)

    def solve_command(self, ntuple):
        """
        Solves a command
        """
        parameters = ntuple['eventDescriptor']
        self.route_event(parameters, "command")


if __name__ == "__main__":
    solver = BasicHesperianProblemSolver(sys.argv[1:])
