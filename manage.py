import pathlib
import sys

sys.path.append(pathlib.Path(__file__).parent)
import config

class Options:
    def crawl(args):
        import src.crawl as c
        c.main()

    def preprocess(args):
        from src.preprocess import Preprocess

        arg = args[0] if len(args) != 0 else None
        Preprocess().run_pipeline(pick_up_from=arg)

    def back_to_midi(args):
        from src.BackToMidi import BackToMidi

        arg = args[0] if len(args) != 0 else None
        BackToMidi().run_pipeline(pick_up_from=arg)

options = {
    "crawl": Options.crawl,
    "preprocess": Options.preprocess,
    "back_to_midi": Options.back_to_midi,
}

def main(args):
    if len(args) == 0:
        print(options.keys())
    else:
        arg = args[0]
        option = options.get(arg)
        if option:
            option(args[1:])
        else:
            raise NameError(f"Option {arg} not found")
        
if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)