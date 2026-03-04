from os import walk
from os.path import join, relpath

from settings import settings


class Storage:
    def __init__(self) -> None:
        self.__path = settings.pending_path

    @property
    def path(self):
        return self.__path

    @property
    def files(self):
        from viewer import viewer
        
        entries = []
        for root, dirs, files in walk(self.path):
            for file in files:
                dir = '' if root == self.path else relpath(root, self.path)
                filepath = join(dir, file)
                entries.append({
                    'name': file,
                    'dir': dir,
                    'filepath': filepath,
                    'uploaded': viewer.find_image(filepath),
                })
        return entries

    def find_file(self, filepath: str):
        files = list(filter(lambda file: file['filepath'].lower() == filepath.lower(), self.files))
        if not len(files):
            raise ValueError("File not found")

        return join(settings.pending_path, files[0]['filepath'])

storage = Storage()
