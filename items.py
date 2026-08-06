from dataclasses import dataclass, field

@dataclass(frozen=True)
class Item:
 
    category: str                 # e.g. "Bit-String Flicking"
    stem: str                     # the question text shown to the student
    answer: str                   # the correct answer
    distractors: list             # [(wrong_answer, error_tag), ...]
    params: dict = field(default_factory=dict)  # difficulty knobs + rng seed
 
    def choices(self, rng):
        opts = [self.answer] + [d[0] for d in self.distractors]
        rng.shuffle(opts)
        return opts
 
    def error_for(self, choice):
        for wrong, tag in self.distractors:
            if wrong == choice:
                return tag
        return None
 
