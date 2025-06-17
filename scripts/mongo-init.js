// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the sports_predictions database
db = db.getSiblingDB('sports_predictions');

// Create collections with validation schemas
db.createCollection('teams', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['team_id', 'name', 'sport'],
      properties: {
        team_id: {
          bsonType: 'string',
          description: 'Unique team identifier'
        },
        name: {
          bsonType: 'string',
          description: 'Team name'
        },
        sport: {
          bsonType: 'string',
          description: 'Sport type'
        },
        league: {
          bsonType: 'string',
          description: 'League name'
        },
        statistics: {
          bsonType: 'object',
          description: 'Team statistics'
        },
        created_at: {
          bsonType: 'date',
          description: 'Creation timestamp'
        },
        updated_at: {
          bsonType: 'date',
          description: 'Last update timestamp'
        }
      }
    }
  }
});

db.createCollection('matches', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['match_id', 'home_team_id', 'away_team_id', 'sport'],
      properties: {
        match_id: {
          bsonType: 'string',
          description: 'Unique match identifier'
        },
        home_team_id: {
          bsonType: 'string',
          description: 'Home team identifier'
        },
        away_team_id: {
          bsonType: 'string',
          description: 'Away team identifier'
        },
        sport: {
          bsonType: 'string',
          description: 'Sport type'
        },
        date: {
          bsonType: 'date',
          description: 'Match date'
        },
        status: {
          bsonType: 'string',
          enum: ['scheduled', 'live', 'finished', 'cancelled'],
          description: 'Match status'
        },
        home_score: {
          bsonType: ['int', 'null'],
          description: 'Home team score'
        },
        away_score: {
          bsonType: ['int', 'null'],
          description: 'Away team score'
        },
        odds: {
          bsonType: 'object',
          description: 'Betting odds'
        },
        predictions: {
          bsonType: 'object',
          description: 'Model predictions'
        }
      }
    }
  }
});

db.createCollection('predictions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['prediction_id', 'match_id', 'model_name', 'prediction'],
      properties: {
        prediction_id: {
          bsonType: 'string',
          description: 'Unique prediction identifier'
        },
        match_id: {
          bsonType: 'string',
          description: 'Associated match identifier'
        },
        model_name: {
          bsonType: 'string',
          description: 'Name of the prediction model'
        },
        prediction: {
          bsonType: 'string',
          enum: ['home_win', 'draw', 'away_win'],
          description: 'Predicted outcome'
        },
        confidence: {
          bsonType: 'double',
          minimum: 0,
          maximum: 1,
          description: 'Prediction confidence score'
        },
        probabilities: {
          bsonType: 'object',
          description: 'Outcome probabilities'
        },
        created_at: {
          bsonType: 'date',
          description: 'Prediction timestamp'
        }
      }
    }
  }
});

db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'telegram_id'],
      properties: {
        user_id: {
          bsonType: 'string',
          description: 'Unique user identifier'
        },
        telegram_id: {
          bsonType: 'long',
          description: 'Telegram user ID'
        },
        username: {
          bsonType: ['string', 'null'],
          description: 'Telegram username'
        },
        first_name: {
          bsonType: ['string', 'null'],
          description: 'User first name'
        },
        preferences: {
          bsonType: 'object',
          description: 'User preferences'
        },
        subscriptions: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'Sport subscriptions'
        },
        created_at: {
          bsonType: 'date',
          description: 'Registration timestamp'
        },
        last_active: {
          bsonType: 'date',
          description: 'Last activity timestamp'
        }
      }
    }
  }
});

// Create indexes for better performance
db.teams.createIndex({ 'team_id': 1 }, { unique: true });
db.teams.createIndex({ 'sport': 1 });
db.teams.createIndex({ 'league': 1 });

db.matches.createIndex({ 'match_id': 1 }, { unique: true });
db.matches.createIndex({ 'sport': 1 });
db.matches.createIndex({ 'date': 1 });
db.matches.createIndex({ 'status': 1 });
db.matches.createIndex({ 'home_team_id': 1, 'away_team_id': 1 });

db.predictions.createIndex({ 'prediction_id': 1 }, { unique: true });
db.predictions.createIndex({ 'match_id': 1 });
db.predictions.createIndex({ 'model_name': 1 });
db.predictions.createIndex({ 'created_at': 1 });

db.users.createIndex({ 'user_id': 1 }, { unique: true });
db.users.createIndex({ 'telegram_id': 1 }, { unique: true });
db.users.createIndex({ 'subscriptions': 1 });

// Create a user for the application (optional)
db.createUser({
  user: 'sports_prediction_app',
  pwd: 'secure_password_here',
  roles: [
    {
      role: 'readWrite',
      db: 'sports_predictions'
    }
  ]
});

print('MongoDB initialization completed successfully!');
