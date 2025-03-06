# Andan-project.-YT-comments
## Тема проекта
Тут будут анализироваться комментарии под видео на ютубе. План минимум -- посмотреть соответствие экспоненциальному закону убывания, немного статистик и кластеризовать комментаторов. Планирую к концу проекта прикрутить немного ml с оценкой тональности комментариев как вот <a href='https://habr.com/ru/articles/599445/'>тут</a>.
## Промежуточный чекпоинт
Я научился вытаскивать комментарии из ютуба с помощью api. В изначальном плане было посмотреть распределение дат регистрации каналов, но пока это не удалось. Api такую информацию не дает, а спарсить вручную я пока не успел. Парсинг осуществляется в parser.py.
Еще нарисованы несколько графиков, посчитано количество комментариев на одного комментатора
## Про парсер
Парсеру нужно принять на вход txt со списком каналов. Есть три режима работы, чтобы сохранать промежуточные результаты: сначала ссылкам сопоставляются id каналов, потом к каждому каналу создается список id видео, и в последнем режиме все собирается в sql
