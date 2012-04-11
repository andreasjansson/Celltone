class Engine:

    def __init__(self, parts, rules):
        self.parts = parts
        self.iteration_length = reduce(lambda x, y: max(x, len(y.notes)), 0)
        self.rules = rules

    def iterate(self):
        polyphony = Polyphony(self.parts, self.iteration_length)
        polyphony.reset_altered()

        for rule in rules:
            for beat in polyphony.beats():
                rule.apply(beat)

        notes = polyphony.notes()
        polyphony.update_pointers()
