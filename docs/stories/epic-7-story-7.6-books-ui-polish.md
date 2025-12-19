# Story 7.6 - Books Pages UI Polish

**Epic**: Epic 7 - E2E Testing & UI Polish  
**Priority**: P1 - High  
**Estimated Effort**: 8 hours  
**Status**: Ready for Review

---

## Dev Agent Record

### Tasks Completed

- [x] Polish BookBrowsePage with error handling, accessibility, and loading states
- [x] Enhance BookCard component with semantic HTML and keyboard navigation
- [x] Improve BookFilterBar with debouncing, clear filters, and active filter count
- [x] Polish PaginationControls with ARIA labels and touch-friendly sizing
- [x] Enhance BookGrid skeleton loaders and empty states
- [x] Add comprehensive accessibility features (ARIA labels, keyboard navigation, focus indicators)
- [x] Implement responsive improvements for all breakpoints
- [x] Add smooth transitions and hover effects (GPU-accelerated)

### Debug Log

- No compilation errors
- All ESLint accessibility warnings resolved
- Semantic HTML elements used where appropriate (article, nav, output, button)

### Completion Notes

Successfully polished all Book browse components with focus on:

1. **Error Handling**: Added retry mechanism with user-friendly error messages
2. **Accessibility**: Full ARIA labels, keyboard navigation, screen reader support
3. **Performance**: GPU-accelerated transitions, lazy loading images, debounced filters
4. **Responsive**: Touch-friendly 44px minimum targets, mobile-optimized layouts
5. **Visual Polish**: Smooth hover effects, consistent card heights, enhanced loading states

### File List

Modified:

- `gajiFE/src/views/BookBrowsePage.vue` - Added error state, semantic HTML, ARIA labels
- `gajiFE/src/components/book/BookCard.vue` - Wrapped in button for accessibility, enhanced focus states
- `gajiFE/src/components/book/BookGrid.vue` - Improved skeleton loaders, added screen reader text
- `gajiFE/src/components/book/BookFilterBar.vue` - Added debouncing, clear filters button, active count
- `gajiFE/src/components/book/PaginationControls.vue` - Enhanced ARIA labels, touch-friendly sizing

### Change Log

1. BookBrowsePage: Error state with retry, semantic `<main>` tag, ARIA labels for regions
2. BookCard: Article with button wrapper for proper semantics, enhanced focus indicators
3. BookFilterBar: 300ms debounce, clear filters button, active filter count display
4. PaginationControls: aria-current for active page, touch-friendly 44x44px buttons
5. BookGrid: output element for status, screen reader text for loading state

### Agent Model Used

Claude Sonnet 4.5

---

## Description

Polish book browse grid layout and book detail Hero section UI

---

## Problem & Opportunity

**Epic 7 Context**: E2E Testing & UI Polish - Week 8-10

**Problem**:

- Unbalanced layout in book list grid
- Lack of visual impact in book detail Hero section
- No image loading state indication
- Mobile responsive design needs improvement
- Missing hover effects and interactions

**Opportunity**:

- Consistent grid layout with PrimeVue DataView
- Enhanced immersion with Hero section background images
- Improved loading UX with Skeleton loader
- Perfect responsive implementation with PandaCSS Grid
- Increased user engagement with hover animations

---

## Proposed Implementation

### Overview

This story focuses on **polish-only** improvements to existing Book-related pages and components. No major UI restructuring - only refinements to loading states, error handling, accessibility, responsive design, and visual consistency.

### Existing Components to Polish

**Files:**

- `gajiFE/src/views/BookBrowsePage.vue`
- `gajiFE/src/components/book/BookCard.vue`
- `gajiFE/src/components/book/BookGrid.vue`
- `gajiFE/src/components/book/BookFilterBar.vue`
- `gajiFE/src/components/book/PaginationControls.vue`

### 1. BookBrowsePage Polish

**Improvements to apply:**

- **Enhanced loading states**:

  - Add skeleton loaders for book cards during initial load
  - Show loading indicator during filter changes
  - Ensure smooth transitions between loading and loaded states

- **Error handling**:

  - Display user-friendly error messages when book fetch fails
  - Add retry mechanism with clear button
  - Show empty state when no books match filters

- **Accessibility enhancements**:

  - Add ARIA labels to filter controls
  - Ensure keyboard navigation works for all interactive elements
  - Add proper heading hierarchy (h1 → h2 → h3)
  - Add alt text to book cover images

- **Responsive improvements**:
  - Verify grid layout adapts properly (1/2/3/4 columns)
  - Ensure touch targets are 44x44px minimum on mobile
  - Test filter bar on small screens

**Example improvements:**

```typescript
// Add error state handling
const error = ref<string | null>(null);

const fetchBooks = async () => {
  loading.value = true;
  error.value = null;

  try {
    books.value = await bookApi.getBooks(currentFilters.value);
  } catch (err) {
    error.value = "Failed to load books. Please try again.";
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const retryFetch = () => {
  fetchBooks();
};
```

### 2. BookCard Component Polish

**Improvements to apply:**

- **Visual polish**:

  - Ensure consistent card heights in grid
  - Add smooth hover transitions (transform, shadow)
  - Improve image loading with placeholder
  - Polish truncation of long titles/descriptions

- **Accessibility**:

  - Add proper semantic HTML (article, h3, etc.)
  - Add aria-label for clickable cards
  - Ensure focus indicators are visible

- **Interactive feedback**:
  - Add loading state for like/bookmark actions
  - Show visual feedback on button clicks
  - Add tooltips for icon buttons

**Example:**

```vue
<template>
  <article
    :class="cardStyles"
    @click="navigateToBook"
    role="button"
    tabindex="0"
    :aria-label="`View details for ${book.title}`"
    @keyup.enter="navigateToBook"
  >
    <div :class="imageContainerStyles">
      <img
        v-if="book.coverUrl"
        :src="book.coverUrl"
        :alt="`${book.title} cover`"
        :class="imageStyles"
        loading="lazy"
      />
      <div v-else :class="placeholderStyles">📚</div>
    </div>
    <!-- Rest of card content -->
  </article>
</template>
```

### 3. BookFilterBar Polish

**Improvements to apply:**

- **UX enhancements**:

  - Add clear all filters button
  - Show active filter count
  - Add filter loading state
  - Ensure filter changes are debounced

- **Accessibility**:

  - Add proper labels to all filter controls
  - Ensure keyboard navigation
  - Add aria-expanded for dropdowns

- **Visual feedback**:
  - Highlight active filters
  - Add transition animations
  - Show result count after filtering

### 4. PaginationControls Polish

**Improvements to apply:**

- **Accessibility**:

  - Add aria-labels to pagination buttons
  - Mark current page with aria-current
  - Ensure keyboard navigation works

- **Visual clarity**:

  - Clear indication of current page
  - Disable prev/next when at boundaries
  - Show page range (e.g., "1-12 of 45")

- **Responsive**:
  - Compact pagination on mobile
  - Ensure touch-friendly button sizes

```vue
<!-- gajiFE/frontend/src/pages/BooksPage.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import DataView from "primevue/dataview";
import Card from "primevue/card";
import Skeleton from "primevue/skeleton";
import Button from "primevue/button";
import Dropdown from "primevue/dropdown";
import { booksService } from "@/services/books";
import { css } from "@/styled-system/css";
import { grid, vstack, flex } from "@/styled-system/patterns";

const router = useRouter();

const books = ref<any[]>([]);
const isLoading = ref(true);
const sortOption = ref("title");

const sortOptions = [
  { label: "제목순", value: "title" },
  { label: "저자순", value: "author" },
  { label: "인기순", value: "popular" },
  { label: "최신순", value: "recent" },
];

const sortedBooks = computed(() => {
  const booksCopy = [...books.value];

  switch (sortOption.value) {
    case "title":
      return booksCopy.sort((a, b) => a.title.localeCompare(b.title));
    case "author":
      return booksCopy.sort((a, b) => a.author.localeCompare(b.author));
    case "popular":
      return booksCopy.sort((a, b) => b.viewCount - a.viewCount);
    case "recent":
      return booksCopy.sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
    default:
      return booksCopy;
  }
});

onMounted(async () => {
  try {
    books.value = await booksService.getAllBooks();
  } catch (error) {
    console.error("Failed to load books:", error);
  } finally {
    isLoading.value = false;
  }
});

const goToBookDetail = (bookId: number) => {
  router.push(`/books/${bookId}`);
};
</script>

<template>
  <div :class="containerStyles">
    <!-- Header -->
    <div :class="headerStyles">
      <h1 :class="titleStyles">책 목록</h1>
      <Dropdown
        v-model="sortOption"
        :options="sortOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="정렬"
        data-testid="sort-dropdown"
      />
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" :class="gridStyles">
      <Card v-for="i in 6" :key="i" :class="cardStyles">
        <template #header>
          <Skeleton width="100%" height="16rem" />
        </template>
        <template #title>
          <Skeleton width="80%" height="1.5rem" />
        </template>
        <template #subtitle>
          <Skeleton width="60%" height="1rem" />
        </template>
        <template #content>
          <Skeleton width="100%" height="4rem" />
        </template>
      </Card>
    </div>

    <!-- Books Grid -->
    <DataView
      v-else
      :value="sortedBooks"
      :layout="'grid'"
      data-testid="books-grid"
    >
      <template #grid="{ data }">
        <div :class="gridStyles">
          <Card
            v-for="book in data"
            :key="book.id"
            :class="bookCardStyles"
            :data-testid="`book-card-${book.id}`"
            @click="goToBookDetail(book.id)"
          >
            <template #header>
              <div :class="coverImageContainerStyles">
                <img
                  :src="book.coverImage || '/default-book-cover.jpg'"
                  :alt="`${book.title} 표지`"
                  :class="coverImageStyles"
                  loading="lazy"
                />
                <div :class="overlayStyles">
                  <Button
                    icon="pi pi-eye"
                    rounded
                    severity="secondary"
                    :class="viewButtonStyles"
                    aria-label="책 보기"
                  />
                </div>
              </div>
            </template>

            <template #title>
              <h3 :class="bookTitleStyles">{{ book.title }}</h3>
            </template>

            <template #subtitle>
              <p :class="authorStyles">{{ book.author }}</p>
            </template>

            <template #content>
              <p :class="descriptionStyles">
                {{ book.description || "설명이 없습니다." }}
              </p>

              <div :class="statsStyles">
                <span :class="statItemStyles" data-testid="scenario-count">
                  <i class="pi pi-lightbulb"></i>
                  {{ book.scenarioCount || 0 }} 시나리오
                </span>
                <span :class="statItemStyles" data-testid="view-count">
                  <i class="pi pi-eye"></i>
                  {{ book.viewCount || 0 }} 조회
                </span>
              </div>
            </template>
          </Card>
        </div>
      </template>
    </DataView>

    <!-- Empty State -->
    <div
      v-if="!isLoading && sortedBooks.length === 0"
      :class="emptyStateStyles"
    >
      <i class="pi pi-inbox" :class="emptyIconStyles"></i>
      <p>등록된 책이 없습니다</p>
    </div>
  </div>
</template>

<style scoped>
const containerStyles = vstack({
  gap: '6',
  padding: '6',
  maxWidth: '7xl',
  margin: '0 auto',
});

const headerStyles = flex({
  justify: 'space-between',
  align: 'center',
  flexWrap: 'wrap',
  gap: '4',
});

const titleStyles = css({
  fontSize: '3xl',
  fontWeight: 'bold',
  color: 'gray.800',
});

const gridStyles = grid({
  columns: { base: 1, sm: 2, md: 3, lg: 4 },
  gap: '6',
  width: 'full',
});

const bookCardStyles = css({
  cursor: 'pointer',
  transition: 'all 0.3s ease',
  height: 'full',
  _hover: {
    transform: 'translateY(-4px)',
    boxShadow: 'xl',
  },
});

const coverImageContainerStyles = css({
  position: 'relative',
  width: 'full',
  aspectRatio: '2/3',
  overflow: 'hidden',
  borderRadius: 'lg',
  bg: 'gray.100',
});

const coverImageStyles = css({
  width: 'full',
  height: 'full',
  objectFit: 'cover',
});

const overlayStyles = flex({
  position: 'absolute',
  inset: '0',
  bg: 'blackAlpha.600',
  justify: 'center',
  align: 'center',
  opacity: '0',
  transition: 'opacity 0.3s ease',
  _groupHover: {
    opacity: '1',
  },
});

const viewButtonStyles = css({
  bg: 'white',
  color: 'blue.600',
});

const bookTitleStyles = css({
  fontSize: 'lg',
  fontWeight: 'semibold',
  color: 'gray.800',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  display: '-webkit-box',
  WebkitLineClamp: '2',
  WebkitBoxOrient: 'vertical',
});

const authorStyles = css({
  fontSize: 'sm',
  color: 'gray.600',
  marginTop: '1',
});

const descriptionStyles = css({
  fontSize: 'sm',
  color: 'gray.700',
  lineHeight: '1.5',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  display: '-webkit-box',
  WebkitLineClamp: '3',
  WebkitBoxOrient: 'vertical',
  marginBottom: '3',
});

const statsStyles = flex({
  gap: '4',
  fontSize: 'sm',
  color: 'gray.500',
});

const statItemStyles = flex({
  gap: '1',
  align: 'center',
});

const emptyStateStyles = vstack({
  gap: '4',
  padding: '12',
  textAlign: 'center',
  color: 'gray.500',
});

const emptyIconStyles = css({
  fontSize: '4xl',
});
</style>
```

### 2. Book Detail Hero Section

```vue
<!-- gajiFE/frontend/src/pages/BookDetailPage.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import Button from "primevue/button";
import Chip from "primevue/chip";
import Skeleton from "primevue/skeleton";
import { booksService } from "@/services/books";
import { scenariosService } from "@/services/scenarios";
import { css } from "@/styled-system/css";
import { vstack, flex, grid } from "@/styled-system/patterns";

const route = useRoute();
const router = useRouter();

const book = ref<any>(null);
const scenarios = ref<any[]>([]);
const isLoading = ref(true);

const bookId = computed(() => parseInt(route.params.id as string));

onMounted(async () => {
  try {
    const [bookData, scenariosData] = await Promise.all([
      booksService.getBookById(bookId.value),
      scenariosService.getScenariosByBookId(bookId.value),
    ]);

    book.value = bookData;
    scenarios.value = scenariosData;
  } catch (error) {
    console.error("Failed to load book:", error);
  } finally {
    isLoading.value = false;
  }
});

const createScenario = () => {
  // Open unified scenario creation modal
  router.push(`/books/${bookId.value}/create-scenario`);
};

const goToScenario = (scenarioId: number) => {
  router.push(`/scenarios/${scenarioId}`);
};
</script>

<template>
  <div>
    <!-- Hero Section with Background -->
    <div v-if="isLoading" :class="heroSkeletonStyles">
      <Skeleton width="100%" height="100%" />
    </div>

    <div
      v-else-if="book"
      :class="heroStyles"
      :style="{
        backgroundImage: `url(${book.coverImage || '/default-hero.jpg'})`,
      }"
    >
      <div :class="heroOverlayStyles"></div>
      <div :class="heroContentStyles">
        <div :class="heroTextStyles">
          <Chip :label="book.genre || '소설'" :class="genreChipStyles" />
          <h1 :class="heroTitleStyles" data-testid="book-title">
            {{ book.title }}
          </h1>
          <p :class="heroAuthorStyles" data-testid="book-author">
            {{ book.author }}
          </p>

          <div :class="heroStatsStyles">
            <div :class="statBadgeStyles">
              <i class="pi pi-lightbulb"></i>
              <span>{{ scenarios.length }} 시나리오</span>
            </div>
            <div :class="statBadgeStyles">
              <i class="pi pi-eye"></i>
              <span>{{ book.viewCount || 0 }} 조회</span>
            </div>
            <div :class="statBadgeStyles">
              <i class="pi pi-users"></i>
              <span>{{ book.readerCount || 0 }} 독자</span>
            </div>
          </div>

          <p :class="heroDescriptionStyles" data-testid="book-description">
            {{ book.description || "이 책에 대한 설명이 없습니다." }}
          </p>

          <Button
            label="시나리오 생성"
            icon="pi pi-plus"
            size="large"
            :class="createButtonStyles"
            @click="createScenario"
            data-testid="create-scenario-button"
          />
        </div>

        <div :class="heroCoverStyles">
          <img
            :src="book.coverImage || '/default-book-cover.jpg'"
            :alt="`${book.title} 표지`"
            :class="coverImageStyles"
          />
        </div>
      </div>
    </div>

    <!-- Scenarios Section -->
    <div :class="scenariosContainerStyles">
      <div :class="scenariosHeaderStyles">
        <h2 :class="sectionTitleStyles">시나리오 목록</h2>
        <p :class="sectionSubtitleStyles">
          이 책의 다양한 What-If 시나리오를 탐험해보세요
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" :class="scenariosGridStyles">
        <div v-for="i in 4" :key="i" :class="scenarioCardStyles">
          <Skeleton width="100%" height="8rem" />
        </div>
      </div>

      <!-- Scenarios Grid -->
      <div v-else-if="scenarios.length > 0" :class="scenariosGridStyles">
        <div
          v-for="scenario in scenarios"
          :key="scenario.id"
          :class="scenarioCardStyles"
          :data-testid="`scenario-card-${scenario.id}`"
          @click="goToScenario(scenario.id)"
        >
          <h3 :class="scenarioTitleStyles">{{ scenario.title }}</h3>
          <p :class="scenarioQuestionStyles">{{ scenario.whatIfQuestion }}</p>

          <div :class="scenarioStatsStyles">
            <span :class="scenarioStatStyles">
              <i class="pi pi-fork"></i>
              {{ scenario.forkCount || 0 }}
            </span>
            <span :class="scenarioStatStyles">
              <i class="pi pi-comments"></i>
              {{ scenario.conversationCount || 0 }}
            </span>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else :class="emptyStateStyles">
        <i class="pi pi-lightbulb" :class="emptyIconStyles"></i>
        <p>아직 생성된 시나리오가 없습니다</p>
        <Button
          label="첫 번째 시나리오 만들기"
          icon="pi pi-plus"
          @click="createScenario"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
const heroSkeletonStyles = css({
  width: 'full',
  height: '500px',
});

const heroStyles = css({
  position: 'relative',
  width: 'full',
  minHeight: '500px',
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  backgroundRepeat: 'no-repeat',
});

const heroOverlayStyles = css({
  position: 'absolute',
  inset: '0',
  bg: 'blackAlpha.700',
});

const heroContentStyles = flex({
  position: 'relative',
  zIndex: '1',
  maxWidth: '7xl',
  margin: '0 auto',
  padding: '12',
  gap: '12',
  align: 'center',
  flexDirection: { base: 'column', md: 'row' },
});

const heroTextStyles = vstack({
  gap: '4',
  alignItems: { base: 'center', md: 'flex-start' },
  textAlign: { base: 'center', md: 'left' },
  flex: '1',
  color: 'white',
});

const genreChipStyles = css({
  bg: 'blue.600',
  color: 'white',
});

const heroTitleStyles = css({
  fontSize: { base: '3xl', md: '5xl' },
  fontWeight: 'bold',
  lineHeight: '1.2',
});

const heroAuthorStyles = css({
  fontSize: { base: 'lg', md: 'xl' },
  color: 'gray.300',
});

const heroStatsStyles = flex({
  gap: '4',
  flexWrap: 'wrap',
});

const statBadgeStyles = flex({
  gap: '2',
  align: 'center',
  bg: 'whiteAlpha.200',
  padding: '2 4',
  borderRadius: 'full',
  fontSize: 'sm',
});

const heroDescriptionStyles = css({
  fontSize: 'md',
  lineHeight: '1.6',
  color: 'gray.200',
  maxWidth: '2xl',
});

const createButtonStyles = css({
  marginTop: '4',
  bg: 'blue.600',
  _hover: {
    bg: 'blue.700',
  },
});

const heroCoverStyles = css({
  width: { base: '200px', md: '300px' },
  flexShrink: '0',
});

const coverImageStyles = css({
  width: 'full',
  aspectRatio: '2/3',
  objectFit: 'cover',
  borderRadius: 'lg',
  boxShadow: '2xl',
});

const scenariosContainerStyles = vstack({
  gap: '6',
  padding: '12',
  maxWidth: '7xl',
  margin: '0 auto',
});

const scenariosHeaderStyles = vstack({
  gap: '2',
  textAlign: 'center',
});

const sectionTitleStyles = css({
  fontSize: '2xl',
  fontWeight: 'bold',
  color: 'gray.800',
});

const sectionSubtitleStyles = css({
  fontSize: 'md',
  color: 'gray.600',
});

const scenariosGridStyles = grid({
  columns: { base: 1, md: 2, lg: 3 },
  gap: '6',
});

const scenarioCardStyles = css({
  padding: '6',
  bg: 'white',
  borderRadius: 'lg',
  boxShadow: 'md',
  cursor: 'pointer',
  transition: 'all 0.3s ease',
  _hover: {
    transform: 'translateY(-2px)',
    boxShadow: 'lg',
  },
});

const scenarioTitleStyles = css({
  fontSize: 'lg',
  fontWeight: 'semibold',
  color: 'gray.800',
  marginBottom: '2',
});

const scenarioQuestionStyles = css({
  fontSize: 'sm',
  color: 'gray.600',
  lineHeight: '1.5',
  marginBottom: '4',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  display: '-webkit-box',
  WebkitLineClamp: '2',
  WebkitBoxOrient: 'vertical',
});

const scenarioStatsStyles = flex({
  gap: '4',
  fontSize: 'sm',
  color: 'gray.500',
});

const scenarioStatStyles = flex({
  gap: '1',
  align: 'center',
});

const emptyStateStyles = vstack({
  gap: '4',
  padding: '12',
  textAlign: 'center',
  color: 'gray.500',
});

const emptyIconStyles = css({
  fontSize: '4xl',
});
</style>
```

---

## 완료 기준(AC)

### BookBrowsePage Polish

- [x] Skeleton loaders display during initial load
- [x] Loading indicator shows during filter changes
- [x] Error message displays with retry button when fetch fails
- [x] Empty state shows when no books match filters
- [x] ARIA labels added to all filter controls
- [x] Keyboard navigation works throughout page
- [x] Proper heading hierarchy (h1 → h2)
- [x] Grid responsive at all breakpoints (1/2/3/4 cols)
- [x] Smooth transitions between states

### BookCard Component Polish

- [x] Consistent card heights in grid layout
- [x] Smooth hover transitions (transform, shadow)
- [x] Image loading with placeholder/fallback
- [x] Long titles/descriptions truncate properly
- [x] Semantic HTML used (article, h3)
- [x] Cards have proper aria-labels
- [x] Visible focus indicators
- [x] Like/bookmark buttons show loading states (N/A - no like/bookmark buttons in current design)
- [x] Visual feedback on button clicks
- [x] Alt text on all images

### BookFilterBar Polish

- [x] Clear all filters button functional
- [x] Active filter count displayed
- [x] Filter changes are debounced
- [x] Proper labels on all controls
- [x] Keyboard navigation functional
- [x] Active filters visually highlighted
- [x] Smooth transition animations
- [x] Result count displayed after filtering

### PaginationControls Polish

- [x] Aria-labels on pagination buttons
- [x] Current page marked with aria-current
- [x] Keyboard navigation works
- [x] Current page clearly indicated
- [x] Prev/next disabled at boundaries
- [x] Page range displayed (e.g., "1-12 of 45")
- [x] Compact layout on mobile
- [x] Touch-friendly button sizes (44x44px min)

### Accessibility (Global)

- [x] All images have alt text
- [x] Keyboard navigation functional
- [x] ARIA attributes correctly implemented
- [x] Focus indicators visible
- [ ] Color contrast meets WCAG AA (Using existing color palette)
- [ ] Screen reader tested (Manual testing required)
- [ ] Hero 섹션 flex-direction 변경 (BookDetailPage not included in this story scope)

### Performance

- [x] 이미지 lazy loading
- [x] Skeleton progressive loading
- [x] 호버 transition (GPU 가속)

---

## 기술 노트

### Key Focus: Polish, Not Restructure

This story is about **incremental improvements** to existing book components. The current structure remains intact:

- BookBrowsePage.vue: Main browse page with filters and grid
- BookCard.vue: Individual book card component
- BookGrid.vue: Grid layout container
- BookFilterBar.vue: Filter controls
- PaginationControls.vue: Pagination UI

### Changes to Apply

**1. Loading State Enhancements**

- Add skeleton loaders (simple div placeholders, no new library needed)
- Implement loading flags for async operations
- Add smooth transitions with CSS

**2. Error Handling**

- Add error state variables
- Display user-friendly messages
- Implement retry mechanisms

**3. Accessibility Additions**

- Add ARIA attributes to interactive elements
- Ensure semantic HTML structure
- Add alt text to images
- Verify keyboard navigation

**4. Visual Polish**

- Refine hover/focus transitions
- Ensure consistent spacing/sizing
- Add visual feedback for interactions
- Test responsive breakpoints

### Implementation Notes

- **No new components**: Work within existing files
- **No layout changes**: Maintain current grid structure
- **Preserve existing styles**: Add polish, don't rewrite
- **Test incrementally**: Verify each improvement works

### Testing Approach

- Manual testing for interactions
- Visual testing at all breakpoints
- Keyboard navigation audit
- Screen reader testing (basic)
- Error scenario testing

### Image Optimization

- **Lazy Loading**: `loading="lazy"` attribute
- **AspectRatio**: CSS aspect-ratio 사용
- **ObjectFit**: cover for consistent sizing
- **Placeholder**: default images for missing covers

### Responsive Grid

- **PandaCSS Grid Pattern**: columns 반응형 설정
- **Breakpoints**: base (mobile), sm (640px), md (768px), lg (1024px)
- **Gap**: 일관된 spacing (24px = gap-6)

### Hero Background

- **Background Image**: inline style binding
- **Overlay**: blackAlpha.700 for text readability
- **Z-index**: content positioned above overlay

---

## 관련 참고자료

- Epic 7: `docs/epics/epic-7-e2e-testing-ui-polish.md`
- Epic 1: Scenario Foundation
- Epic 3: Scenario Discovery
- PrimeVue DataView: https://primevue.org/dataview/
- PandaCSS Grid: https://panda-css.com/docs/patterns/grid

---

## 관련 이슈·블로커

**Dependencies**:

- Epic 3 completed (Book Browse & Discovery) ✅
- BookBrowsePage.vue exists ✅
- BookCard, BookGrid, BookFilterBar components exist ✅
- No new libraries required

**Blockers**:

- None

**Parallel Work**:

- Story 7.5: Auth & Navigation UI Polish
- Story 7.7: Chat UI Polish
- Story 7.8: Profile & Search UI Polish

**Notes**:

- This is a polish-only story - no major structural changes
- Focus on loading states, error handling, and accessibility
- Work within existing component structure

**Dependencies**:

- Epic 1 완료 (Scenario System)
- Epic 3 완료 (Discovery)
- PrimeVue 설정
- PandaCSS 설정

**Blockers**:

- None

**Parallel Work**:

- Story 7.7: Chat UI Polish
- Story 7.8: Profile & Search UI Polish
