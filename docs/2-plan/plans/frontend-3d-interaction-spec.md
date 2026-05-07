# Frontend 3D Interaction Specification

## 1. Overview

This document outlines the technical and design specifications for integrating immersive 3D interactions into the Gaji platform promotional pages. The goal is to enhance user engagement and convey the brand innovative and organic identity through "Scrollytelling" and interactive 3D elements.

## 2. Technical Stack

- **Framework**: Vue 3 (Composition API)
- **3D Engine**: Three.js
- **Vue Adapter**: TresJS (@tresjs/core)
- **3D Utilities**: @tresjs/cientos (OrbitControls, GLTFLoaders, etc.)
- **Animation**: GSAP (GreenSock Animation Platform) with ScrollTrigger
- **Styling**: PandaCSS (existing project standard)

## 3. Page Specifications

### 3.1. Login Page (The Fourth Wall)

**Layout**:

- **Initial State**: Split screen (50% Left / 50% Right).
- **Interaction Flow**:
  1.  **Expansion Phase**: As the user starts scrolling (0px - 500px), the Left Column expands to cover the full width (100%), and the Right Column fades out. The 3D scene remains in its initial "Book" state.
  2.  **Storytelling Phase**: Once fully expanded, further scrolling drives the 3D animation timeline (The Book -> Release -> Formation -> Invitation).
- **Right Column (50%)**: Functional area. Contains the Login form. Sticky positioning to remain visible while scrolling.
- **Left Column (50% -> 100%)**: Experiential area. A tall scrollable container that drives the animation timeline.

**3D Scene (The Stage)**:

- **Concept**: "The Story of Connection" (연결의 이야기)
- **Visuals & Interactions (Sequenced by Scroll)**:

  - **Stage 1 (0% - 25%)**: **The Book (책)**.

    - **Visual**: 수많은 파티클들이 모여 **책의 형상**을 이루고 있으며, 이전의 블랙 팔레트를 대신해 **메탈릭 골드** 톤으로 빛납니다. (정적인 3D 모델이 아닌, 파티클로 구성된 책)
    - **Interaction**: 스크롤에 따라 파티클들이 흩어질 준비를 하며 미세하게 진동합니다.

  - **Stage 2 (25% - 50%)**: **The HandScroll (핸드 스크롤)**.

    - **Visual**: 책에서 흩어진 파티클들이 **스크롤 제스처를 연상시키는 두 개의 고리(Torus)** 형태로 얽히며 연결과 환영의 의미를 표현합니다.
    - **Particles**: **Rings (Torus)** 형태의 파티클이 주를 이룹니다.

  - **Stage 3 (50% - 75%)**: **The Closed Book (닫힌 책)**.

    - **Visual**: 파티클들이 한 번 더 모여 **완전히 닫힌 책** 형태를 만들며, 페이지가 스치듯 닫히는 동작을 통해 새로운 챕터가 시작될 준비를 보여줍니다.
    - **Particles**: **Plates (Flat Boxes)** 형태로 가장자리의 두께감을 표현하고, 책 등 부분에는 골드 엣지를 강조합니다.

  - **Stage 4 (75% - 100%)**: **The Sparkles (반짝이)**.

    - **Visual**: 파티클들이 **나선형 은하(Spiral Galaxy)**처럼 폭발하며 화면 가득 반짝이며, 전체가 **골드 플레어**를 띠어 1단계와 톤을 맞춥니다.
    - **Particles**: **Diamonds (Octahedrons)** 형태의 파티클이 마법 같은 피날레를 장식하되, 금박 같은 하이라이트를 유지합니다.

- **Technical Approach**:
  - Use **InstancedMesh** for all stages to ensure high performance with 1200+ particles.
  - Use **GSAP** to animate particle positions between defined shapes (Book -> HandScroll -> Closed Book -> Galaxy).

**Component Structure**:

- `AuthLayout.vue`: Wrapper component handling the split layout and scroll container.
- `The3DLoginStage.vue`: TresJS canvas component containing the 3D scene for Login.

### 3.2. Register Page (The Growth of Imagination)

**Layout**:

- **Initial State**: Split screen (50% Left / 50% Right).
- **Interaction Flow**:
  1.  **Expansion Phase**: As the user starts scrolling (0px - 500px), the Left Column expands to cover the full width (100%), and the Right Column fades out. The 3D scene remains in its initial "Seed" state.
  2.  **Storytelling Phase**: Once fully expanded, further scrolling drives the 3D animation timeline (The Seed -> Growth -> Forest).
- **Right Column (50%)**: Functional area. Contains the Register form. Sticky positioning to remain visible while scrolling.
- **Left Column (50% -> 100%)**: Experiential area. A tall scrollable container that drives the animation timeline.

**3D Scene (The Stage)**:

- **Concept**: "The Growth of Imagination" (상상의 성장)
- **Visuals & Interactions (Sequenced by Scroll)**:

  - **Stage 1 (0% - 25%)**: **The Sprout (새싹)**. A small, glowing green sprout rotates gently. Represents the "Seed" of a story.
    - **구현 세부사항**: 현실적인 새싹 모양을 위해 구체와 토러스 조합이 아닌, 여러 개의 얇은 실린더를 사용하여 떡잎과 줄기 형태로 구성. 부드러운 곡선을 위해 TubeGeometry 고려.
  - **Stage 2 (25% - 50%)**: **The Branching (가지 뻗기)**. The sprout grows rapidly into a tree trunk, and branches extend outwards. Represents "Infinite Possibilities".
    - **구현 세부사항**: 스크롤 진행도에 따라 나무 줄기의 높이(scaleY)가 점진적으로 증가하는 애니메이션 적용. 가지들도 함께 위로 성장하며 펼쳐지는 효과 추가.
  - **Stage 3 (50% - 75%)**: **The Spark (전구)**. A 3D lightbulb appears (or hangs from a branch) and lights up brightly. Represents "AI & Imagination".
    - **구현 세부사항**: 초기 상태에서는 전구가 작고 불이 꺼진 상태(emissiveIntensity: 0). 스크롤이 내려갈수록 bulbScale과 bulbIntensity가 점진적으로 증가하여 전구가 커지고 밝아지는 효과 구현.
  - **Stage 4 (75% - 100%)**: **The Foliage (나뭇잎)**. Lush leaves pop into existence at the ends of the branches, completing the tree. Represents "Completing the World".
    - **구현 세부사항**: 단순한 구체 대신 납작한 타원형(SphereGeometry의 scale 조정) 또는 PlaneGeometry를 활용하여 실제 나뭇잎처럼 보이도록 구현. 여러 잎들을 가지 끝에 배치하고 회전 적용.

- **Technical Approach**:
  - Use **Procedural Geometries** (CylinderGeometry, SphereGeometry, TubeGeometry) via TresJS to create these shapes dynamically without external assets.
  - **GSAP** will drive the properties (scale, rotation, intensity) based on the scroll progress.

**Component Structure**:

- `AuthLayout.vue`: Wrapper component handling the split layout and scroll container.
- `The3DRegisterStage.vue`: TresJS canvas component containing the 3D scene for Register.

### 3.3. About Page (Cinematic Journey)

**Layout**: Full-page scrolling sections.

**Section 1: Hero (Brand Identity)**

- **Visual**: Large, floating 3D Typography ("Gaji") or the Brand Logo in 3D.
- **Interaction**: Slowly rotates/floats. Reacts to scroll by zooming out to reveal the next section.

**Section 2: Mission (Core Values)**

- **Concept**: "Growing Together"
- **Visual**: A procedural 3D forest or a network of connected nodes.
- **Interaction**:
  - **Fly-through**: Scroll triggers a camera movement forward through the 3D space.
  - **Reveal**: Passing specific depth markers triggers text (Core Values) to fade in/up.

**Section 3: How to Use (Feature Showcase)**

- **Visual**: A 3D abstract representation of a "Scenario" or "Book".
- **Interaction**:
  - **Step-by-Step**: Scroll rotates the object to show different facets, symbolizing different features (Writing, Reading, Sharing).
  - **Assembly**: Elements come together to form a complete book/scenario object.

## 4. Performance & Accessibility

- **Loading**: Use `Suspense` for async 3D model/texture loading with a fallback spinner.
- **Mobile**:
  - Simplify or disable complex 3D effects on mobile devices to ensure performance.
  - Fallback to static high-quality images or simple CSS animations if WebGL is not supported.
- **Reduced Motion**: Respect `prefers-reduced-motion` media query by disabling auto-rotation or rapid movements.

## 5. Implementation Roadmap

1.  **Setup**: Install `three`, `@tresjs/core`, `@tresjs/cientos`, `gsap`.
2.  **POC**: Create `The3DAuthStage.vue` with a basic rotating cube driven by GSAP ScrollTrigger.
3.  **Integration**: Apply to Login/Register pages.
4.  **Refinement**: Replace basic shapes with custom shaders or better materials.
5.  **Expansion**: Build the About page scenes.
