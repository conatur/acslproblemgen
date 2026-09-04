
#let _seed = state("acsl-seed", "")
#let _title = state("acsl-title", [])

// A fill-in-the-blank rule, e.g. for the name field.
#let _rule(width) = box(
  width: width,
  baseline: 0.25em,
  line(length: 100%, stroke: 0.4pt),
)

// One numbered problem: prompt, the expression in monospace, then either
// lettered choices or blank space to work in.
#let problem(prompt, expression, choices, show-choices, work-space) = {
  prompt
  if expression != none {
    block(above: 0.8em, below: 0.8em, text(font: "DejaVu Sans Mono", expression))
  }
  if show-choices {
    enum(
      numbering: "(A)",
      tight: false,
      spacing: 0.5em,
      ..choices.map(c => text(font: "DejaVu Sans Mono", c)),
    )
  } else {
    v(work-space) // room to work
  }
}

// One student's sheet: name field, then the numbered problems. The seed goes
// in the running header, so it stays in the corner even if a student's
// problems spill onto a second page.
#let student-page(student, show-choices, work-space) = {
  _seed.update(student.seed)

  grid(
    columns: (1fr, auto),
    align: (left + bottom, right + bottom),
    [Name: #_rule(2.5in)],
    [Date: #_rule(1.25in)],
  )
  v(0.4em)
  line(length: 100%, stroke: 0.4pt + luma(60%))
  v(0.8em)

  enum(
    tight: false,
    spacing: 1.6em,
    ..student.problems.map(p => problem(
      p.prompt,
      p.expression,
      p.choices,
      show-choices,
      work-space,
    )),
  )
}

// The whole batch: every student in one document, one page break between
// students. Thirty students is still a single compile.
#let worksheet(
  title: [ACSL Practice],
  students: (),
  show-choices: true,
  work-space: 1.5in,
) = {
  _title.update(title)

  set page(
    paper: "us-letter",
    margin: 1in,
    header: context {
      set text(size: 8pt, fill: luma(45%))
      grid(
        columns: (1fr, auto),
        align: (left, right),
        _title.get(),
        [seed #raw(_seed.get())],
      )
    },
    footer: context {
      set align(center)
      set text(size: 8pt, fill: luma(45%))
      counter(page).display("1")
    },
  )
  set text(size: 11pt)
  set par(justify: false)

  for (i, student) in students.enumerate() {
    if i > 0 { pagebreak() }
    align(center, {
      text(size: 15pt, weight: "bold", title)
      linebreak()
      text(size: 11pt, student.label)
    })
    v(1em)
    student-page(student, show-choices, work-space)
  }
}
