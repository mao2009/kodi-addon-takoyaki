import importlib

from takoyaki import Takoyaki


class Takoyaki(Takoyaki):
    def run(self):
        module_name = self.params.get('module_name')
        if self.params.get("mode") == "module_list_mode":
            self.module_list_mode()
        else:
            importlib.import_module(module_name).open()
    
