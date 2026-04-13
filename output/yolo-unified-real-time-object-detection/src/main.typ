// 번역본: You Only Look Once: Unified, Real-Time Object Detection (Redmon et al., arXiv:1506.02640v5)
#set page(paper: "a4", margin: (x: 2.2cm, y: 2.2cm))
#set text(
  lang: "ko",
  font: ("Malgun Gothic", "New Computer Modern"),
  size: 10.5pt,
  hyphenate: false,
  cjk-latin-spacing: auto,
)
#set par(
  justify: false,
  leading: 1.32em,
  spacing: 22pt,
  first-line-indent: 0pt,
  linebreaks: "optimized",
)
#set list(spacing: 0.9em)
#show regex("[가-힣a-zA-Z0-9]+"): it => box(it)
#set heading(numbering: "1.")
#show figure.where(kind: table): set figure.caption(position: top)
#show heading.where(level: 1): it => {
  v(0.8em)
  it
  v(0.4em)
}
#show heading.where(level: 2): it => {
  v(0.6em)
  it
  v(0.3em)
}
#show heading.where(level: 3): it => {
  v(0.4em)
  it
  v(0.25em)
}

#align(center)[
  #text(size: 15pt, weight: "bold")[단 한 번만 본다: 통합적 실시간 객체 검출 #text(size: 11pt, weight: "regular")[(You Only Look Once: Unified, Real-Time Object Detection)]]
  #v(1em)
]

#align(center)[
  #set par(leading: 0.65em)
  Joseph Redmon\* · Santosh Divvala\*† · Ross Girshick¶ · Ali Farhadi\*† \
  University of Washington\* · Allen Institute for AI† · Facebook AI Research¶ \
  #link("http://pjreddie.com/yolo/")[http://pjreddie.com/yolo/]
]

#v(0.8em)
#par(first-line-indent: 0pt)[
  #text(weight: "bold")[초록] \
  본 논문은 객체 검출(object detection)에 대한 새로운 접근인 YOLO(You Only Look Once)를 제시한다. 기존 객체 검출 연구는 분류기를 재활용하여 검출을 수행한다. 이에 대해 본 연구는 객체 검출을 공간적으로 분리된 경계 상자와 이에 대응하는 클래스 확률에 대한 회귀 문제로 정식화한다. 단일 신경망이 한 번의 평가로 전체 영상으로부터 경계 상자와 클래스 확률을 직접 예측한다. 검출 파이프라인 전체가 단일 네트워크이므로 검출 성능에 대해 끝에서 끝까지 최적화할 수 있다. \
  통합 구조는 매우 빠르다. 기본 YOLO 모델은 초당 45프레임으로 실시간에 가깝게 영상을 처리한다. 더 작은 네트워크인 Fast YOLO는 초당 155프레임을 처리하면서도 다른 실시간 검출기 대비 mAP(mean average precision)의 두 배에 해당하는 성능을 달성한다. 최첨단 검출 시스템과 비교하면 YOLO는 국소화(localization) 오류는 더 많이 내지만 배경에 대한 거짓 양성(false positive)을 예측할 가능성은 더 낮다. 마지막으로 YOLO는 객체에 대한 매우 일반적인 표현을 학습하며, 자연 영상에서 다른 영역(예: 예술 작품)으로 일반화할 때 DPM 및 R-CNN 등 다른 검출 방법을 능가한다.
]

#v(0.6em)
#align(center)[
  #text(size: 9pt)[arXiv:1506.02640v5 [cs.CV] 2016년 5월 9일]
]

#pagebreak()

#include "sec-intro.typ"
#include "sec-unified.typ"
#include "sec-compare.typ"
#include "sec-exp.typ"
#include "sec-wild.typ"
#include "sec-conc.typ"
#include "sec-refs.typ"
