# SGR Agent v2.1 — Claude Code Skill / Implementation Brief

Ты — Claude Code, работающий как инженер-исполнитель по реализации **SGR Agent v2.1**.
Твоя задача — **спроектировать и реализовать рабочий Python-проект** по спецификации ниже.
Ты не должен упрощать архитектуру до single-pass агента. Нужен именно **многофазный детерминированный пайплайн**.

Главная цель: построить надежный агентный runtime, где **каждая фаза — отдельный LLM-вызов с собственной schema-first валидацией**, а любые файловые изменения проходят через Step Verifier.

---

## 1. Что именно нужно сделать

Реализуй production-ready каркас проекта для **SGR Agent v2.1** со следующими свойствами:

1. **Classifier phase**
   - принимает `Task(text, context)`
   - возвращает `TaskClass`
   - поддерживает fast-exit сценарии

2. **Planner phase**
   - строит `Plan` из списка `Step`
   - использует `plans.yaml` как источник шаблонов/паттернов
   - использует `mistake_log.yaml` как источник анти-паттернов

3. **Executor loop**
   - идет по `plan.steps`
   - для каждого шага вызывает Executor LLM
   - делает dispatch tool-call
   - перед любым изменением ФС обязательно вызывает Verifier
   - умеет correction / replan

4. **Outcome Judge**
   - проверяет, завершена ли задача корректно
   - если нет, разрешает mini-fix loop максимум 2 раза
   - если после этого still fail → `OUTCOME_ERR_INTERNAL`

5. **Mistake Logger**
   - пишет новые правила/ошибки в `mistake_log.yaml`
   - лог должен быть пригоден для повторного использования между запусками

6. **Tool runtime / dispatch layer**
   - реализует набор tool request/response примитивов
   - как минимум для:
     - context
     - tree
     - find
     - search
     - list
     - read
     - write
     - delete
     - mkdir
     - move
     - report_task_completion

7. **Schema-first orchestration**
   - все LLM-ответы должны парситься через Pydantic модели
   - `reasoning` всегда первое поле в каждой релевантной модели
   - ветвление — через schema/discriminators, а не через расплывчатые prompt-инструкции

8. **Безопасность файловых операций**
   - агент **никогда** не должен писать в файловую систему без прохождения Step Verifier
   - это должно быть enforced на уровне runtime, а не только текста prompt

---

## 2. Основные архитектурные принципы

Не отходи от этих принципов:

### A. Deterministic pipeline
Пайплайн строго фазовый:
- CLASSIFIER
- (optional fast exit)
- PLANNER
- EXECUTOR LOOP
- OUTCOME JUDGE
- MISTAKE LOGGER

### B. CoT через порядок полей
Во всех Pydantic-схемах, где есть reasoning, поле `reasoning` должно идти **первым**.
Это важно и должно быть явно соблюдено в коде.

### C. Routing через схему
Используй `Literal`, `Union`, discriminator-friendly структуры.
Не прячь основную маршрутизацию в prose prompt logic, если она может быть выражена схемой.

### D. Runtime guardrails > prompt-only rules
Критичные ограничения должны enforce'иться кодом:
- запрет write/delete/move без verifier
- ограничение retry count
- ограничение размера плана
- защита от бесконечных циклов

### E. Learnable memory between runs
`mistake_log.yaml` и `plans.yaml` должны быть внешними ресурсами проекта, не hardcoded в коде.

### F. Extensible design
Проект должен быть подготовлен для будущей Rust migration:
- чистые интерфейсы
- минимум скрытой магии
- отделение моделей, orchestration, llm client и tools

---

## 3. Целевая структура проекта

Сгенерируй проект примерно такой структуры (можно уточнить, если есть более удачный вариант, но смысл должен сохраниться):

```text
sgr_agent/
  pyproject.toml
  README.md
  plans.yaml
  mistake_log.yaml
  src/sgr_agent/
    __init__.py
    config.py
    models.py
    enums.py
    prompts/
      classifier.md
      planner.md
      executor.md
      verifier.md
      judge.md
      mistake_logger.md
    llm/
      base.py
      client.py
      structured.py
    tools/
      __init__.py
      base.py
      dispatcher.py
      filesystem.py
      search.py
      reporting.py
      safety.py
    phases/
      classifier.py
      planner.py
      executor.py
      verifier.py
      judge.py
      mistake_logger.py
    orchestration/
      runner.py
      state.py
      plan_cache.py
      guards.py
    storage/
      yaml_store.py
    utils/
      logging.py
      paths.py
      hashing.py
  tests/
    test_models.py
    test_classifier_fast_exit.py
    test_planner.py
    test_verifier_guards.py
    test_executor_loop.py
    test_outcome_judge.py
    test_mistake_logger.py


    вызов агента описан в pac1-py/main.py