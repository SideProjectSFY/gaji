# System Class Diagram

## Domain Model

The class diagram below represents the core entity relationships in the Gaji backend.

### Key Entities
- **Novel**: Represents the source book/story.
- **RootUserScenario**: A user-created alternative timeline based directly on a Novel.
- **LeafUserScenario**: A fork of a RootUserScenario.
- **Conversation**: A chat session within a scenario.
- **User**: The platform user.

```mermaid
classDiagram
    class User {
        +UUID id
        +String username
        +String email
        +List~UserFollow~ followers
    }

    class Novel {
        +UUID id
        +String title
        +String author
        +String genre
        +Integer publicationYear
    }

    class RootUserScenario {
        +UUID id
        +String title
        +String whatIfQuestion
        +String characterChanges
        +String eventAlterations
        +String settingModifications
        +Integer forkCount
        +Boolean isPrivate
    }

    class LeafUserScenario {
        +UUID id
        +String title
        +String whatIfQuestion
        +Boolean isPrivate
    }

    class Conversation {
        +UUID id
        +String characterVectordbId
        +Boolean isRoot
        +Boolean hasBeenForked
        +Integer messageCount
        +Boolean isPrivate
    }

    class Message {
        +UUID id
        +String content
        +String role
        +LocalDateTime createdAt
    }

    %% Relationships
    User "1" --> "*" RootUserScenario : creates
    User "1" --> "*" LeafUserScenario : creates
    User "1" --> "*" Conversation : participates

    Novel "1" ..> "*" RootUserScenario : basis for

    RootUserScenario "1" <|-- "*" LeafUserScenario : parent
    
    RootUserScenario "1" --> "*" Conversation : context
    LeafUserScenario "1" --> "*" Conversation : context

    Conversation "1" --> "*" Message : contains
    Conversation "1" --> "0..1" Conversation : parent (forks)
```

## Notes
- **Novel Content**: The actual text content of novels is stored separately in a Vector Database (VectorDB), not in the relational `Novel` table.
- **Characters**: Character definitions are also stored in VectorDB. `Conversation` entities reference characters via `characterVectordbId`.
- **Scenario Hierarchy**: 
    - `RootUserScenario` is a direct modification of a `Novel`.
    - `LeafUserScenario` is a modification of a `RootUserScenario` (Max Depth: 1).
