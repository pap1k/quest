import os, json


class UserProgress:
    userId: int = 0
    is_input: bool = False
    is_photo_requested: bool = False
    is_video_requested: bool = False
    script_id: int = -1
    line_n: int = 0
    compare_with: str = ""

    def __init__(self, id: int) -> None:
        self.userId = id
        self.is_input = False
        self.is_photo_requested = False
        self.is_video_requested = False
        self.script_id = 0
        self.line_n = 0
        self.compare_with = ""


class Progress:
    progresses: list[UserProgress] = []
    backup_file = "_backup.json"

    def __init__(self) -> None:
        if self.restore():
            print("Succesfully restored progress data")

    def remove(self, user: UserProgress):
        self.progresses = list(filter(lambda x: x != user, self.progresses))

    def get(self, userid) -> UserProgress:
        for user in self.progresses:
            if user.userId == userid:
                return user
        return None

    def new(self, userid) -> UserProgress:
        self.progresses.append(UserProgress(userid))
        self.do_backup()
        return self.get(userid)

    def to_json_str(self):
        data = {}
        for user in self.progresses:
            data[user.userId] = {
                "input": user.is_input,
                "is_photo_requested": user.is_photo_requested,
                "is_video_requested": user.is_video_requested,
                "script_id": user.script_id,
                "line_n": user.line_n,
                "compare_with": user.compare_with,
            }
        return json.dumps(data)

    def restore(self):
        if not os.path.exists(self.backup_file):
            return False
        with open(self.backup_file, "r", encoding="utf-8") as f:
            data = f.read()
            if data == "":
                return False
            j = json.loads(data)
            for id in j:
                u = UserProgress(int(id))
                u.is_input = j[id]["input"]
                u.is_photo_requested = j[id]["is_photo_requested"]
                u.is_video_requested = j[id]["is_video_requested"]
                u.script_id = j[id]["script_id"]
                u.line_n = j[id]["line_n"]
                u.compare_with = j[id]["compare_with"]
                self.progresses.append(u)
            return True

    def do_backup(self):
        with open(self.backup_file, "w", encoding="utf-8") as f:
            f.write(self.to_json_str())
