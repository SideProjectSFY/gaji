# Test User Accounts

Mock user data for development and E2E testing purposes.

## Common Credentials

**Password for ALL test users:** `password123`  
**BCrypt Hash (strength 12):** `$2b$12$yyWWM.U.dFk5swMLsaYLBuFIe2x8N8shIcSTFl7Y9aNaH2PXze6rC`

## Available Test Users

### 1. Jane Austen

- **Email:** `jane.austen@gaji.com`
- **Username:** `jane_austen`
- **User ID:** `550e8400-e29b-41d4-a716-446655440001`
- **Bio:** Lover of classic literature and romantic tales. Currently exploring Pride and Prejudice scenarios.
- **Use Case:** Romance genre enthusiast, main character scenarios

### 2. Detective Holmes

- **Email:** `sherlock.holmes@gaji.com`
- **Username:** `detective_holmes`
- **User ID:** `550e8400-e29b-41d4-a716-446655440002`
- **Bio:** Master detective and mystery enthusiast. Investigating the most intriguing plot twists in literature.
- **Use Case:** Mystery genre testing, investigation scenarios

### 3. Fantasy Explorer

- **Email:** `fantasy.lover@gaji.com`
- **Username:** `fantasy_explorer`
- **User ID:** `550e8400-e29b-41d4-a716-446655440003`
- **Bio:** Lost in fantastical worlds. Currently diving deep into Tolkien and Rowling universes.
- **Use Case:** Fantasy genre testing, world-building scenarios

### 4. Midnight Reader

- **Email:** `horror.fan@gaji.com`
- **Username:** `midnight_reader`
- **User ID:** `550e8400-e29b-41d4-a716-446655440004`
- **Bio:** Gothic horror enthusiast. Reading Dracula and Frankenstein under the moonlight.
- **Use Case:** Horror genre testing, dark atmosphere scenarios

### 5. Time Traveler

- **Email:** `scifi.geek@gaji.com`
- **Username:** `time_traveler`
- **User ID:** `550e8400-e29b-41d4-a716-446655440005`
- **Bio:** Science fiction aficionado. Exploring alternate timelines in classic sci-fi literature.
- **Use Case:** Sci-Fi genre testing, timeline scenarios

### 6. Book Collector

- **Email:** `book.collector@gaji.com`
- **Username:** `book_collector`
- **User ID:** `550e8400-e29b-41d4-a716-446655440006`
- **Bio:** Avid reader with a diverse collection spanning all genres. Always seeking the next great story.
- **Use Case:** Multi-genre testing, collection features

### 7. New Reader

- **Email:** `new.reader@gaji.com`
- **Username:** `new_reader`
- **User ID:** `550e8400-e29b-41d4-a716-446655440007`
- **Bio:** Just started my journey into interactive literature. Excited to explore!
- **Use Case:** Onboarding flow testing, beginner user experience

### 8. Story Weaver

- **Email:** `story.writer@gaji.com`
- **Username:** `story_weaver`
- **User ID:** `550e8400-e29b-41d4-a716-446655440008`
- **Bio:** Aspiring writer learning from the masters. Creating my own alternative storylines.
- **Use Case:** Scenario creation testing, writer persona

### 9. History Enthusiast

- **Email:** `history.buff@gaji.com`
- **Username:** `history_enthusiast`
- **User ID:** `550e8400-e29b-41d4-a716-446655440009`
- **Bio:** Historical fiction lover. Reimagining pivotal moments in classic literature.
- **Use Case:** Historical genre testing, period-specific scenarios

### 10. Test User

- **Email:** `test.user@gaji.com`
- **Username:** `test_user`
- **User ID:** `550e8400-e29b-41d4-a716-446655440010`
- **Bio:** Test account for E2E testing and development purposes.
- **Use Case:** General E2E testing, automated tests

## Usage Examples

### Login via API

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane.austen@gaji.com",
    "password": "password123"
  }'
```

**Response:**

```json
{
  "accessToken": "eyJhbGciOiJIUzM4NCJ9...",
  "refreshToken": "eyJhbGciOiJIUzM4NCJ9...",
  "userId": "550e8400-e29b-41d4-a716-446655440001",
  "email": "jane.austen@gaji.com",
  "username": "jane_austen"
}
```

### Login via Frontend

1. Navigate to login page
2. Enter email: `jane.austen@gaji.com`
3. Enter password: `password123`
4. Click login

## Database Query

```sql
-- View all test users
SELECT username, email, bio FROM users ORDER BY created_at;

-- Login as specific user
SELECT id, email, username FROM users WHERE email = 'jane.austen@gaji.com';
```

## Migration Information

- **Migration File:** `V40__add_user_mock_data.sql`
- **Applied:** 2025-12-18
- **Total Users:** 10
- **Password Hash:** BCrypt with strength 10
