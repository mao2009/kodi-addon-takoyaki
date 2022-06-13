from takoyaki import Takoyaki


class Takoyaki(Takoyaki):
    def run(self):
        modes = self.get_mode_list()
        self.select_mode(modes)