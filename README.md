# Backend и моделирование

## Описание репозитория

- Частичная загрузка данных источников
- Формирование статичных графиков
- Кросс-валидация модели краткосрочного прогноза
- Backend-часть, отвечающая за моделирование краткосрочных сценариев
- Скрипты, отвечающие за генерацию графиков для Frontend

## Общее описание технологий

| Поле                  | Значение            | Комментарий                                                                                                                                                                                                                                                                                                            |
| --------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Язык программирования | **Python 3.8**      | Окружение собирается при помощи [Anaconda](https://docs.conda.io/en/latest/miniconda.html), команда `conda create env -f environment.yml`                                                                                                                                                                              |
| Backend               | **FastAPI**         | [Сайт](https://fastapi.tiangolo.com/)                                                                                                                                                                                                                                                                                  |
| Работа с БД           | **SQLAlchemy**      | [Сайт](https://www.sqlalchemy.org/)                                                                                                                                                                                                                                                                                    |
| Табличные данные      | **Pandas**          | [Документация](https://pandas.pydata.org/docs/)                                                                                                                                                                                                                                                                        |
| Линейная алгебра      | **NumPy**/**SciPy** | [Документация](https://numpy.org/)                                                                                                                                                                                                                                                                                     |
| Данные котировок      | **yfinance**        | [Репозиторий GitHub](https://github.com/ranaroussi/yfinance)                                                                                                                                                                                                                                                           |
| Статичные графики     | **matplotlib**      | [Документация](https://matplotlib.org/)                                                                                                                                                                                                                                                                                |
| Интерактивные графики | **plotly**          | [Документация](https://plotly.com/python/)                                                                                                                                                                                                                                                                             |
| Временные ряды        | **fbprophet**       | Решение от Facebook, реализщует идеи, предложенные в работе [Taylor, Sean J., and Benjamin Letham. "Forecasting at scale." The American Statistician 72.1 (2018): 37-45.](https://www.tandfonline.com/doi/abs/10.1080/00031305.2017.1380080). [Документация](https://facebook.github.io/prophet/docs/quick_start.html) |

## Детальное описание блоков

### Загрузка данных из источников

Тут [реализована](https://github.com/graphometrica/minenergo-models/blob/master/runnable/load_yahoo_data.py) загрузка данных котировок и фьючерсов.

Мы загружаем:

- [Нефть - `CR=F`](https://finance.yahoo.com/quote/CL=F?p=CL=F&.tsrc=fin-srch)
- [Алюминий - `ALI=F`](https://finance.yahoo.com/quote/ALI=F?p=ALI=F&.tsrc=fin-srch)
- [Природный газ - `NG=F`](https://finance.yahoo.com/quote/NG=F?p=NG=F&.tsrc=fin-srch)
- [Медь - `HG=F`](https://finance.yahoo.com/quote/HG=F?p=HG=F&.tsrc=fin-srch)
- [Акции Газпрома - `OGZPY`](https://finance.yahoo.com/quote/OGZPY?p=OGZPY&.tsrc=fin-srch)
- [Акции РУСАЛ - `RUAL.ME`](https://finance.yahoo.com/quote/RUAL.ME?p=RUAL.ME&.tsrc=fin-srch)
- [Пара Рубль/Доллар - `RUB=X`](https://finance.yahoo.com/quote/RUB=X?p=RUB=X&.tsrc=fin-srch)

### Backend модели краткосрочного прогнозирования и моделирования

Тут [WEB-приложение](https://github.com/graphometrica/minenergo-models/blob/master/main.py) по краткосрочному прогнозированию.

Логика работы:

- При старте сразу кешируем исторические данные из база, так как там ~800,000 строк: почасовые данные в течении года по каждому из регионов.
- При обращении со стороны Frontend идет проверка наличия свежей версии закешированной модели для выбранного региона
- Если модели нет, то она обучается с нуля [код обучения](https://github.com/graphometrica/minenergo-models/blob/master/scripts/model_scripts.py#L44), если модель уже есть, то она берется из кеша (т.к. обучение сейчас порядка десятков секунд)
- Берется кешированная версия для предсказаний и в ней заменяются ожидаемые значения признаков, если с Frontend пришел запрос на моделирование сценария. [Код генерации стандартного набора данных для предсказаний](https://github.com/graphometrica/minenergo-models/blob/master/scripts/model_scripts.py#L27), [код замены признаков и предсказания](https://github.com/graphometrica/minenergo-models/blob/master/scripts/model_scripts.py#L62)
- Генерируются графики, в зависимости от выбранного типа: [Статичные](https://github.com/graphometrica/minenergo-models/blob/master/scripts/plot_scripts.py) [Интерактивные](https://github.com/graphometrica/minenergo-models/blob/master/scripts/plot_plotly_scripts.py)

### Кросс-валидация

Код [для полной кросс-валидации](https://github.com/graphometrica/minenergo-models/blob/master/runnable/make_cross_validation.py). Из-за большой вычислительной нагрузки и долгого времени работы (порядка нескольких минут на одну модель, т.е. на один субъект РФ) вынесен из Backend в оффлайн-исполняемый файл.

Все сгенерированные результаты находятся [тут](https://github.com/graphometrica/minenergo-models/tree/master/plots)
