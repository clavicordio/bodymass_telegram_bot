from src.datautils import date_format
import src.config as config

COMMAND_LIST = "/enter_weight - ввести текущий вес\n\n" \
               "/plot - показать график (за 2 недели) \n" \
               "/plot_all - показать график (за всё время) \n" \
               "/download - скачать данные (*.csv) \n" \
               "/upload - загрузить данные в бота (*.csv)\n" \
               "/erase - стереть все данные \n\n" \
               "/start - показать меню \n\n" \
               "/info - информация и советы по использованию бота"

ENTER_WEIGHT_BUTTON = "Ввести свой вес"
ENTER_WEIGHT_COMMANDS = ['/enter_weight', ENTER_WEIGHT_BUTTON]

SHOW_MENU_BUTTON = 'Показать меню'
SHOW_MENU_COMMANDS = ['/start', SHOW_MENU_BUTTON]

INFO = "Этот бот разработан, чтобы помочь вам на фитнес-пути. " \
       "Просто регулярно взвешивайтесь и отправляйте мне результаты.\n\n" \
       "Вес тела сильно варьируется от дня к дню (до ~3 кг). " \
       "Это происходит в основном из-за задержки пищи и жидкости. " \
       "Так что, если вы взвесите себя, а затем просто посмотрите на весы на следующий день, " \
       "к сожалению, вы не получите представления о том, сколько килограммов ткани вы фактически набрали или потеряли. " \
       "Для эффективного отслеживания прогресса " \
       "необходимо измерять массу тела по крайней мере <b>3 раза в неделю (желательно, каждый день)</b> и " \
       "записывать результаты. " \
       "Также рекомендуется взвешиваться примерно в одно и то же время суток. " \
       "После того, как вы взвешивались не менее 2 недель подряд, вам нужно посмотреть на " \
       "<a href=\"https://ru.wikipedia.org/wiki/%D0%9B%D0%B8%D0%BD%D0%B8%D0%B8_%D1%82%D1%80%D0%B5%D0%BD%D0%B4%D0%B0\">линию тренда</a>. " \
       "Таким образом, вы получите реальное представление о том, происходит ли у вас потеря или набор веса, " \
       "и с какой скоростью. \n\n" \
       "Миссия этого бота - сделать вышеописанный процесс <b>максимально легким</b>. " \
       "Просто достаньте свой телефон и отправьте мне пару цифр. " \
       "Проще не придумаешь. \n\n" \
       "Помните, в фитнесе главное - постоянство, и <b>чем меньше ненужного сопротивления вы встречаете, " \
       "тем более устойчивыми становятся ваши привычки в долгосрочной перспективе.</b>\n\n" \
       "Кстати, ориентировочно, вы должны стремиться " \
       "к <b>0,5-1 кг в неделю</b> для <b>похудения</b>, " \
       "и к <b>0,2-0,5 кг в неделю</b> для <b>набора массы</b>, если хотите делать это без риска для здоровья. " \
       "Но лучше всего проконсультироваться с тренером или диетологом, так как эти цифры зависят " \
       "от различных факторов (пол, возраст, общее состояние здоровья). "


HELLO = "Привет, я бот, разработанный для отслеживания веса тела и помощи в достижении фитнес-целей. " \
        "Пожалуйста, выберите команду ниже.\n\n"

HOW_MUCH_DO_YOU_WEIGH = "Сколько вы сегодня весите?"

YOU_ARE_MAINTAINING = "\nВы в настоящее время <i>поддерживаете</i> свой вес тела.\n"
YOU_ARE_SURPLUS = "\nВ настоящее время у вас <i>избыток калорий</i>.\n"
YOU_ARE_DEFICIT = "\nВ настоящее время у вас <i>дефицит калорий</i>.\n"

YOU_ARE_GAINING_TEMPLATE = "Вы набираете вес со средней скоростью <i>%.2f кг/неделю</i>\n"
YOU_ARE_LOSING_TEMPLATE = "Вы теряете вес со средней скоростью <i>%.2f кг/неделю</i>\n"

WHICH_IS_TOO_SLOW = "(что слишком медленно для классификации как избыток или дефицит)\n"

PLEASE_ENTER_VALID_POSITIVE_NUMBER = "Пожалуйста, введите действительное положительное число (ваш вес тела в кг) /start"

SUCCESSFULLY_ADDED_NEW_ENTRY = "Успешно добавлена новая запись:"

HERE_PLOT_LAST_TWO_WEEKS = "Вот график вашего прогресса за последние две недели.\n"
HERE_PLOT_OVERALL_PROGRESS = "Вот график вашего общего прогресса.\n"

NO_DATA_TO_DOWNLOAD_YET = "У вас пока нет данных для загрузки.\n\n" \
                          "Используйте команду /enter_weight ежедневно. \n" \
                          "Или, используйте команду /upload для загрузки существующих данных."

HERE_ALL_YOUR_DATA = "<b>Вот все ваши данные.</b>"
YOU_CAN_ANALYZE_OR_BACKUP = "Вы можете проанализировать их сами или использовать их в качестве резервной копии " \
                            "для /upload в случае потери данных."

REPLY_UPLOAD = "Вы можете загрузить существующие данные о весе, предоставив мне таблицу в формате *.csv."
REPLY_UPLOAD += "Таблица должна содержать два столбца:\n"
REPLY_UPLOAD += "- Дата в формате " + date_format + "\n"
REPLY_UPLOAD += "- Вес тела\n"
REPLY_UPLOAD += "Вы можете загрузить пример, используя команду /download. \n\n"
REPLY_UPLOAD += "Для продолжения загрузки, отправьте мне действительный файл в формате *.csv."
REPLY_UPLOAD += "\n\n/start - вернуться в меню"

NO_VALID_DOCUMENT = "Вы не прислали действительный документ.\n/start"


FILE_TOO_BIG = f"Файл слишком большой (максимальный размер {config.MAX_FILE_SIZE // 1024} кб)\n/start"
FILE_INVALID = "Файл недействителен. Используйте команду /download, чтобы получить пример действительного файла.\n" \
               "/start"
FILE_UNEXPECTED_ERROR = "Произошла неожиданная ошибка во время обработки файла. Извините.\n/start"


DATA_UPLOADED_SUCCESSFULLY = "<b>Данные успешно загружены.</b>\nПосмотрите на график."

CONFIRMATION_WORD = "да"

REPLY_ERASE = 'Вы собираетесь <b>стереть все ваши данные</b>. '
REPLY_ERASE += 'Это действие нельзя отменить.\n\n'
REPLY_ERASE += f'<b>Пожалуйста, подтвердите, введя <i>{CONFIRMATION_WORD}</i></b>.\n\n'
REPLY_ERASE += '/start - вернуться'

CANCEL_DELETE = 'Хорошо, отменяю удаление.'

NO_DATA_YET = "У вас пока нет данных."

ERASE_COMPLETE = 'Хорошо, я забыл всё о вашем прогрессе.\n' \
                 'Но держите файл с данными, которые я только что стёр - на всякий случай.'

UNEXPECTED_DOCUMENT = "Неожиданный документ. " \
                      "Вы хотите, чтобы я загрузил данные о вашем весе? Используйте команду /upload."

BODYWEIGHT_PLOT_LABEL = 'Масса тела, кг'
