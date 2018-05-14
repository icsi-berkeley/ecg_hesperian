"""
"Subclasses" text_agent.
"""

from nluas.language.text_agent import *


class HesperianTextAgent(TextAgent):
  def __init__(self, args):
    CoreAgent.__init__(self, args)
    self.transport = Transport(self.name)

    self.clarification_content = None
    self.clarification_type = None
    self.prev_query = None
    self.sid = None

    self.solver_destination = "{}_{}".format(self.federation, "ProblemSolver")
    self.transport.subscribe(self.solver_destination, self.callback)
    self.original = None
    self.print_usage()

  def print_usage(self):
    self.output_stream("Usage",
      "To quit enter 'q'\n\
       To destroy the current session ID enter 'killsession'\n\
       To respond to a clarification/synonym question begin your response with 'c:'\n\
       Otherwise, all input issues queries")

  def prompt(self):
    ntuple = {'clarification': False, 'synonyms': False, 'sid': self.sid}
    msg = input("> ")
    if msg == "q":
      self.close(True)
    elif msg == None or msg =="":
      pass
    elif msg == "killsession":
      self.sid = None
    elif msg[0:2].lower() == "c:":
      ntuple['query'] = self.prev_query
      self.handle_clarification(msg[2:], ntuple)
    else:
      ntuple['query'] = msg.strip()
      self.prev_query = ntuple['query']
      self.transport.send(self.solver_destination, ntuple)

  def handle_clarification(self, msg, ntuple):
    if self.clarification_type == None:
      return self.output_stream("Error", "No clarification question has been issued.")
    elif self.clarification_type == "SYNONYM":
      originals = self.clarification_content
      synonyms = msg.strip().split(',')
      if len(synonyms) != len(originals):
        return self.output_stream("Error", "The number of synonyms does not match the number of unknown words.")
      else:
        ntuple['synonyms'] = ["{}>{}".format(original, synonym) for (original, synonym) in zip(originals, synonyms)]
    elif self.clarification_type == "QUESTION":
      options = self.clarification_content['options'].lower().split("|")
      if msg.strip().lower() not in options:
        return self.output_stream("Error", "That is not a valid option for the multiple choice question.")
      else:
        idx = options.index(msg.strip().lower())
        ntuple['clarification'] = {'field': self.clarification_content['field'],
                                   'val': self.clarification_content['options'].split("|")[idx]}
    self.transport.send(self.solver_destination, ntuple)

  def callback(self, ntuple):
    """ Callback for receiving information from ProblemSolver. """
    self.clarification_type = None
    if 'sid' in ntuple:
      self.sid = ntuple['sid']
    if self.is_quit(ntuple):
      return self.close()
    elif self.cannot_analyze(ntuple):
      return
    elif self.unknown_word(ntuple):
      return
    elif self.queries(ntuple):
      return self.clarification(ntuple)
    else:
      raise Error("Should not reach this point")

  def cannot_analyze(self, ntuple):
    if "failure_type" in ntuple and ntuple['failure_type'] == "CANNOT_ANALYZE":
      self.output_stream("Error", ntuple['error'])
      return True
    return False

  def unknown_word(self, ntuple):
    if "failure_type" in ntuple and ntuple['failure_type'] == "UNKNOWN_WORD":
      self.output_stream("Error", "Unknown words in input. Please provide a comma separated list \
                                   of synonyms for the following words: {}".format(ntuple['failures']))
      self.clarification_type = "SYNONYM"
      self.clarification_content = ntuple['failures']
      return True
    return False

  def queries(self, ntuple):
    if "queries" in ntuple:
      printed = 0
      print("QUERIES:")
      for query in ntuple['queries']:
        print(query)
        printed += 1
        if printed == 5:
          break
      print("\n")
      return True
    return False

  def clarification(self, ntuple):
    if 'clarification' in ntuple:
      self.clarification_type = "QUESTION"
      self.clarification_content = ntuple['clarification']
      print("CLARIFICATION:")
      self.output_stream(ntuple['clarification']['text'], ntuple['clarification']['options'])
    else:
      self.clarification_type = None

  def output_stream(self, tag, message):
    print("{}: {}\n".format(tag, message))

if __name__ == "__main__":
  text = HesperianTextAgent(sys.argv[1:])
  text.keep_alive(text.prompt)
