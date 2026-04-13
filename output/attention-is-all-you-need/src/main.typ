// 번역본: Attention Is All You Need (Vaswani et al., arXiv:1706.03762v7)
#set page(paper: "a4", margin: (x: 2.2cm, y: 2.2cm))
#set text(
  lang: "ko",
  font: ("Malgun Gothic", "New Computer Modern"),
  size: 10.5pt,
  hyphenate: false,
  cjk-latin-spacing: auto,
)
// 한글: 양쪽 정렬 시 글자 간격·줄나눔이 과해져 음절 단위로 끊기기 쉬움 → 배열(왼쪽 정렬).
#set par(
  justify: false,
  leading: 1.2em,
  spacing: 14pt,
  first-line-indent: 0pt,
  linebreaks: "optimized",
)
#set list(spacing: 0.9em)
// 한글·영문·숫자로 이어진 토큰은 줄 중간에서 쪼개지지 않도록 박스로 묶음(CSS keep-all에 가까운 효과; 공백·구두점에서만 끊김).
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
  #text(size: 9pt)[적절한 출처 표기가 있는 경우, Google은 본 논문의 표와 그림을 저널리즘 또는 학술 목적으로만 복제할 수 있도록 허용한다.]
  #v(1.2em)
  #text(size: 15pt, weight: "bold")[어텐션만으로 충분하다 #text(size: 11pt, weight: "regular")[(Attention Is All You Need)]]
  #v(1em)
]

#align(center)[
  #set par(leading: 0.65em)
  Ashish Vaswani\* · Google Brain · avaswani\@google.com \
  Noam Shazeer\* · Google Brain · noam\@google.com \
  Niki Parmar\* · Google Research · nikip\@google.com \
  Jakob Uszkoreit\* · Google Research · usz\@google.com \
  Llion Jones\* · Google Research · llion\@google.com \
  Aidan N. Gomez\*† · University of Toronto · aidan\@cs.toronto.edu \
  Łukasz Kaiser\* · Google Brain · lukaszkaiser\@google.com \
  Illia Polosukhin\*‡ · illia.polosukhin\@gmail.com
]

#v(0.8em)
#par(first-line-indent: 0pt)[
  #text(weight: "bold")[초록] \
  지배적인 순열 변환(sequence transduction) 모델은 인코더와 디코더를 포함한 복잡한 순환 신경망이나 합성곱 신경망에 기반한다. 성능이 가장 좋은 모델은 또한 인코더와 디코더를 어텐션(attention) 메커니즘으로 연결한다. 본 논문은 순환과 합성곱을 전부 배제하고 오직 어텐션 메커니즘만에 기반한 새로운 단순 네트워크 구조인 트랜스포머(Transformer)를 제안한다. 두 가지 기계 번역 과제에 대한 실험에서, 제안 모델은 품질 면에서 우수하면서 병렬화 가능성이 더 크고 학습 시간이 현저히 짧음을 보여 준다. WMT 2014 영어-독일어 번역 과제에서 본 모델은 BLEU 28.4를 달성하여, 앙상블을 포함한 기존 최고 결과보다 2 BLEU 이상 향상시켰다. WMT 2014 영어-프랑스어 번역 과제에서는 8개의 GPU로 3.5일 학습한 뒤 단일 모델 BLEU 41.8이라는 새로운 최첨단 점수를 기록했으며, 이는 문헌의 최고 모델들에 비해 학습 비용의 극히 일부에 해당한다. 넓은 학습 데이터와 제한된 학습 데이터 모두에서 영어 구문 분석(constituency parsing)에 성공적으로 적용함으로써, 트랜스포머가 다른 과제에도 잘 일반화됨을 보였다.
]

#v(0.6em)
#par(first-line-indent: 0pt)[
  #set text(size: 9pt)
  \*기여 동등. 저자 순서는 무작위이다. Jakob은 RNN을 자기-어텐션으로 바꾸자고 제안하고 이 아이디어를 평가하려는 노력을 시작했다. Ashish는 Illia와 함께 최초의 트랜스포머 모델을 설계·구현했으며 이 연구의 모든 측면에 핵심적으로 관여했다. Noam은 스케일된 내적 어텐션, 다중 헤드 어텐션, 매개변수 없는 위치 표현을 제안했으며 거의 모든 세부에 함께 관여한 또 다른 사람이 되었다. Niki는 원본 코드베이스와 tensor2tensor에서 수많은 모델 변형을 설계·구현·튜닝·평가했다. Llion은 새로운 모델 변형 실험, 초기 코드베이스, 효율적 추론과 시각화를 담당했다. Łukasz와 Aidan은 tensor2tensor의 여러 부분 설계와 구현, 이전 코드베이스 대체, 결과 대폭 개선과 연구 가속에 수많은 날을 보냈다. \
  †본 연구는 Google Brain 재직 시 수행. \
  ‡본 연구는 Google Research 재직 시 수행.
]

#align(center)[
  #v(0.5em)
  #text(size: 9pt)[제31회 신경정보처리시스템학회(NIPS 2017), 롱비치, CA, 미국.]
]

#pagebreak()

#include "sec-intro.typ"
#include "sec-bg.typ"
#include "sec-model.typ"
#include "sec-why.typ"
#include "sec-train.typ"
#include "sec-res.typ"
#include "sec-conc.typ"
#include "sec-ack.typ"
#include "sec-refs.typ"
#include "sec-appendix.typ"
