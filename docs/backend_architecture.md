# Backend Layered Architecture (Strict DDD & Clean Architecture)

This document outlines the architectural standards for the backend services, specifically focusing on the separation of concerns between the Domain and Infrastructure layers using the Repository pattern.

## Overview

We follow a **Strict Domain-Driven Design (DDD)** approach combined with **Clean Architecture** principles. The core idea is that the **Domain Layer** must not depend on any external frameworks or technologies (like Spring Data JPA, Hibernate, etc.).

## Repository Pattern Implementation

To achieve strict separation, we use the **Repository Adapter Pattern**.

### 1. Domain Layer (Pure Java)
*   **Location**: `domains/{domain-name}/src/main/java/com/gaji/{domain}/domain/repository/`
*   **File**: `{Entity}Repository.java`
*   **Characteristics**:
    *   Pure Java Interface.
    *   **NO** `extends JpaRepository`.
    *   **NO** Spring Data dependencies visible in signatures (except simple types or project-defined DTOs).
    *   Defines explicitly what the domain needs (save, findById, complex domain queries).

```java
package com.gaji.chat.domain.repository;

import com.gaji.chat.domain.model.Conversation;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import java.util.Optional;
import java.util.UUID;

public interface ConversationRepository {
    Conversation save(Conversation conversation);
    Optional<Conversation> findById(UUID id);
    // ... explicit methods
}
```

### 2. Infrastructure Layer (Implementation & Persistence)
*   **Location**: `domains/{domain-name}/src/main/java/com/gaji/{domain}/infrastructure/persistence/`
*   **Files**:
    1.  `{Entity}JpaRepository.java` (Spring Data Interface)
    2.  `{Entity}RepositoryImpl.java` (Adapter Implementation)

#### A. Spring Data JPA Interface
*   Internal to the infrastructure layer.
*   Extends `JpaRepository` and `QuerydslPredicateExecutor` (if needed).
*   Handles actual DB interaction.

```java
package com.gaji.chat.infrastructure.persistence;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ConversationJpaRepository extends JpaRepository<Conversation, UUID> {
    // Spring Data Magic Methods & @Query
}
```

#### B. Repository Implementation (Adapter)
*   Implements the **Domain Repository** interface.
*   Injects the **JPA Repository**.
*   Delegates calls to the JPA repository or uses QueryDSL/Native SQL for complex logic.

```java
package com.gaji.chat.infrastructure.persistence;

import com.gaji.chat.domain.repository.ConversationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class ConversationRepositoryImpl implements ConversationRepository {
    
    private final ConversationJpaRepository jpaRepository;
    private final JPAQueryFactory queryFactory;

    @Override
    public Conversation save(Conversation conversation) {
        return jpaRepository.save(conversation); // Delegate
    }
    
    // ... implementations
}
```

## Benefits
1.  **Decoupling**: The domain logic is 100% independent of persistence technology. We can switch from JPA to JDBC, MongoDB, or in-memory storage without changing a single line of domain code.
2.  **Testability**: Domain services can easily mock the repository interface without dealing with JPA complexities.
3.  **Clarity**: The repository interface reveals exactly what persistent operations are available to the domain, rather than exposing hundreds of unwanted Spring Data methods.

## Migration Guide for Existing Domains
1.  Move Persistence logic to `infrastructure/persistence`.
2.  Refactor `DomainRepository` to be a pure interface.
3.  Create `InfraJpaRepository` for Spring Data support.
4.  Create `InfraRepositoryImpl` to bridge the two.
