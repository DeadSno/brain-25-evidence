# Архитектурные диаграммы

> Формальные UML-диаграммы проекта. Рендерятся автоматически на GitHub через Mermaid.
> Основной контекст — [ARCHITECTURE.md](../ARCHITECTURE.md).

## 1. Use Case Diagram — кто и что делает с системой

```mermaid
flowchart LR
    User([Пользователь])
    Dev([Внешний разработчик])
    Maint([Maintainer])
    LLM([LLM / Agent])

    subgraph Brain["Brain 25 Evidence"]
        UC1([Просмотреть карточку])
        UC2([Фильтровать по грейду])
        UC3([Изучить механизмы])
        UC4([Проверить взаимодействия])
        UC5([Скачать полный датасет])
        UC6([Прочитать метаданные API])
        UC7([Добавить новую добавку])
        UC8([Обновить full texts])
        UC9([Обогатить данные через ETL])
        UC10([RAG по 11900 статьям])
    end

    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4

    Dev --> UC5
    Dev --> UC6

    Maint --> UC7
    Maint --> UC8
    Maint --> UC9

    LLM --> UC6
    LLM --> UC10