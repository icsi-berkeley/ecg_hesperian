import time
import uuid

class User(object):
  def __init__(self, uid):
    self.data = {}
    self.queries = {}

    self.set('created_at', int(time.time()))
    self.set('updated_at', int(time.time()))
    self.set('uid', uid)

  def __contains__(self, key):
    return key in self.data

  def get(self, key):
    if key in self.data:
      return self.data[key]
    return None

  def set(self, key, value):
    assert(value != None)
    self.data[key] = value
    self.data['updated_at'] = int(time.time())
    return self

  def touch(self):
    self.data['updated_at'] = int(time.time())

class HesperianData(object):
  def __init__():
    self.sid_to_uid = {}
    self.users = {}
    self.expired_uids = []
    self.reserved_keys = set(['created_at', 'updated_at', 'raw_queries', 'improved_queries'])

  def create_user(self):
    """
    Creates a user object, creates an sid and uid, and maps the sid to the uid
    """
    sid = uuid.uuid4()
    uid = uuid.uuid4()
    user = User(uid)

    self.users[uid] = user
    self.sid_to_uid[sid] = (uid, int(time.time()))
    return sid

  def delete_user(self, sid):
    uid = self._get_uid(sid)
    if uid != None:
      self.expired_uids.append(uid)
      del self.sid_to_uid[sid]

  def _get_user(self, uid):
    assert(uid in self.users)
    return self.users[uid]

  def _get_uid(self, sid):
    if sid in self.sid_to_uid:
      return self.sid_to_uid[sid][0]
    return None

  def touch(self, sid):
    if sid in self.sid_to_uid:
      self.sid_to_uid[sid][1] = int(time.time())
      self._get_user(self._get_uid(sid)).touch()
      return True
    return False

  def set_data(self, sid, key, value):
    if key not in self.reserved_keys:
      uid = self._get_uid(sid)
      if uid != None and value != None:
        self._get_user(uid).set(key, value)
        return True
    return False

  def get_data(self, sid, key):
    uid = self._get_uid(sid)
    if uid != None and value != None:
      return self._get_user(uid).get(key)
    return None

  def add_query(self, sid, original, improved):
    qid = "query:" + str(time.time())
    query_data = {
      "original": original,
      "improved": improved,
      "feedback": []
    }
    if self.set_data(sid, qid, query_data):
      return qid
    return None

  def add_feedback(self, sid, qid, url, feedback_data):
    query_data = self.get_data(self, sid, qid)
    if query_data:
      query_data["feedback"].append((url, feedback_data))
      return True
    return False
