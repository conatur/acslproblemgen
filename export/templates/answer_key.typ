// ACSL practice answer key — the match for worksheet.typ.
//
// Deliberately dense: several students per page, each block headed by the
// same seed printed on that student's worksheet, so a teacher can pair a key
// block to a sheet at a glance.
//
// As in worksheet.typ, every content value arrives pre-escaped from the
// Python side; this file owns layout only.
//
// Data shape:
//   students: ( (label: content, seed: str, answers: (answer, ...)), ... )
//   answer:   (letter: content or none, value: content, notes: (note, ...))
//   note:     (label: content or none, value: content, tag: content)

// One student's block: heading, seed, then a tight numbered answer list.
#let student-block(student, show-rationale) = {
  block(
    breakable: false,
    below: 1.2em,
    {
      block(
        width: 100%,
        fill: luma(94%),
        inset: (x: 6pt, y: 4pt),
        radius: 2pt,
        grid(
          columns: (1fr, auto),
          align: (left, right),
          text(weight: "bold", size: 10pt, student.label),
          text(size: 8pt, fill: luma(35%), [seed #raw(student.seed)]),
        ),
      )
      v(0.4em)
      enum(
        tight: true,
        spacing: if show-rationale { 0.7em } else { 0.35em },
        ..student.answers.map(a => {
          if a.letter != none { [(#a.letter) ] }
          text(font: "DejaVu Sans Mono", a.value)
          // Why each distractor is wrong — off by default to keep the key
          // compact, since the app already shows this feedback on screen.
          if show-rationale and a.notes.len() > 0 {
            block(above: 0.35em, inset: (left: 0.6em), text(size: 8pt, fill: luma(35%),
              a.notes
                .map(n => {
                  if n.label != none { [(#n.label) ] }
                  raw(n.value)
                  [ — ]
                  n.tag
                })
                .join(linebreak()),
            ))
          }
        }),
      )
    },
  )
}

#let answer-key(
  title: [ACSL Practice],
  students: (),
  show-rationale: false,
  column-count: 2,
) = {
  set page(
    paper: "us-letter",
    margin: 0.75in,
    header: context {
      set text(size: 8pt, fill: luma(45%))
      grid(
        columns: (1fr, auto),
        align: (left, right),
        [#title — ANSWER KEY],
        counter(page).display("1"),
      )
    },
  )
  set text(size: 10pt)

  align(center, text(size: 14pt, weight: "bold", [#title — Answer Key]))
  v(0.8em)

  columns(column-count, gutter: 1.4em, {
    for student in students {
      student-block(student, show-rationale)
    }
  })
}
