class Overmind:

    def analyse(self, memory, ranked):

        weak = ranked[-5:]

        return {
            "goal": "Improve weakest entities",
            "targets": [e["name"] for e in weak]
        }
