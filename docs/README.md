# LifeWeeksBot Architecture Documentation

This directory contains C4 model diagrams for the LifeWeeksBot system architecture.

## Diagrams Overview

### 1. System Context Diagram (`system-context-diagram.puml`)
Shows the LifeWeeksBot system in its environment, including:
- **Telegram User**: The end user interacting with the bot
- **LifeWeeksBot**: The main system container
- **External Systems**: Telegram Bot API, SQLite Database, APScheduler

### 2. Container Diagram (`container-diagram.puml`)
Shows the high-level technical building blocks of the LifeWeeksBot system:
- **LifeWeeksBot Application**: Main Python application
- **Command Handlers**: Handles user commands and interactions
- **Life Calculator**: Calculates life weeks and statistics
- **Database Service**: Manages user data and settings
- **Scheduler Service**: Manages weekly notifications
- **Message Service**: Handles message localization and formatting

### 3. Component Diagram (`component-diagram.puml`)
Shows the components within each container:
- **Application Components**: Main app, handler registry, text handler
- **Handler Components**: Individual command handlers (start, weeks, visualize, etc.)
- **Calculator Components**: Life calculator, visualizer, statistics engine
- **Database Components**: Database service, repositories, migration service
- **Scheduler Components**: Notification scheduler, schedule manager, notification sender
- **Message Components**: Message generator, localization, message formatter

## Technology Stack

- **Language**: Python 3.12
- **Bot Framework**: python-telegram-bot 20.7
- **Database**: SQLite with SQLAlchemy 2.0
- **Migrations**: Alembic
- **Scheduler**: APScheduler
- **Visualization**: Matplotlib
- **Image Processing**: Pillow

## Key Features

1. **Life Week Tracking**: Calculate and display weeks lived since birth
2. **Visualization**: Generate life progress charts and statistics
3. **Multi-language Support**: Russian, English, Ukrainian, Belarusian
4. **Weekly Notifications**: Automated weekly reminders
5. **User Settings**: Customizable birth date, language, and notification preferences
6. **Subscription Management**: Basic and premium subscription tiers

## Architecture Principles

- **Separation of Concerns**: Each component has a single responsibility
- **Dependency Injection**: Services are injected where needed
- **Repository Pattern**: Database operations are abstracted through repositories
- **Handler Pattern**: Command handling is organized through dedicated handlers
- **Service Layer**: Business logic is separated from presentation logic

## How to View Diagrams

1. **Online PlantUML Editor**: Copy the .puml content to [PlantUML Online Editor](http://www.plantuml.com/plantuml/uml/)
2. **VS Code Extension**: Install PlantUML extension for VS Code
3. **Local PlantUML**: Install PlantUML locally and generate images

## System Boundaries

- **Internal System**: All Python code and local SQLite database
- **External Dependencies**: Telegram Bot API, Matplotlib library
- **User Interface**: Telegram chat interface
- **Data Storage**: Local SQLite database with user profiles and settings