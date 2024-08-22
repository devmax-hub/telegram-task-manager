import logging

from django.db import models
import os

from django.db.models.signals import post_save
from django.dispatch import receiver
from dotenv import load_dotenv
from django.db.models import Count, Q
import random

load_dotenv()
from aiogram import Bot

API_TOKEN = os.getenv('TOKEN')
bot = Bot(token=API_TOKEN)

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

POSITION_CHOICES = [
    ('copywriter', 'Копирайтер'),
    ('mobilograph', 'Мобилограф'),
    ('editor', 'Монтажер'),
    ('designer', 'Дизайнер'),
    ('smm', 'СММ'),
    ('marketer', 'Маркетолог'),
    ('admin', 'Администратор'),
]

LEVEL_CHOICES = [
    ('junior', 'junior'),
    ('middle', 'middle'),
    ('senior', 'senior'),
]
STATUS_CHOICES = [
    ('новое', 'Новое'),
    ('в процессе', 'В процессе'),
    ('завершено', 'Завершено'),
    ('просрочено', 'Просрочено'),
    ('отменено', 'Отмен')
]
WORKFLOW_ORDER = ['copywriter', 'mobilograph', 'editor', 'designer', 'smm', 'marketer', 'admin']


class Employee(models.Model):
    surname = models.CharField(max_length=50, verbose_name="Фамилия")
    name = models.CharField(max_length=50, verbose_name="Имя")
    middle_name = models.CharField(max_length=50, verbose_name="Отчество", blank=True, null=True)
    status = models.BooleanField(verbose_name="Статус", default=False,
                                 help_text="Используйте для включения/выключения сотрудника.")
    comment = models.TextField(verbose_name="Описание", blank=True, null=True)
    strike = models.IntegerField(verbose_name="Штрафные баллы", default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано в", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено в", blank=True, null=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, verbose_name="Уровень", default='junior', blank=True)
    position = models.CharField(max_length=255, choices=POSITION_CHOICES, verbose_name="Должность")
    # account = models.CharField(max_length=255, verbose_name="Логин", unique=True, blank=True, null=True)
    iin = models.CharField(max_length=255, verbose_name="ИИН", unique=True)
    chat_id = models.CharField(max_length=50, verbose_name="Идентификатор чата", unique=True, blank=True, null=True)
    phone = models.CharField(max_length=15, verbose_name="Телефон", unique=True)
    email = models.EmailField(verbose_name="Почта", unique=True, blank=True, null=True)
    telegram = models.CharField(max_length=255, verbose_name="Телеграм", unique=True, null=True, blank=True)
    rating = models.IntegerField(verbose_name="Рейтинг", default=5)
    is_confirmed = models.BooleanField(verbose_name="Подтверждение", default=False,
                                       help_text="Так же используйте что бы запретить вход в систему.")

    def save(self, *args, **kwargs):
        logging.info(f"Args: {args}, Kwargs: {kwargs}")
        super().save(*args, **kwargs)
        if not Balance.objects.filter(employee=self).exists():
            Balance.objects.create(employee=self, balance=0)

    class Meta:
        verbose_name = 'сотрудника'
        verbose_name_plural = 'Сотрудники'

    @property
    def fio(self):
        return f"{self.surname} {self.name} {self.middle_name}"

    def __str__(self) -> str:
        return f"{self.fio}"


class Task(models.Model):
    name = models.CharField(max_length=255, verbose_name="Задача")
    description = models.TextField(verbose_name="Описание", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано в", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено в", blank=True, null=True)
    # file_path = models.CharField(max_length=255, verbose_name="Путь к файлу", blank=True, null=True)
    file = models.FileField(max_length=100, blank=True, null=True, verbose_name="Файл", upload_to='downloads/')
    link = models.URLField(verbose_name="Ссылка", blank=True, null=True)

    class Meta:
        verbose_name = 'задачу'
        verbose_name_plural = 'Задачи'

    def __str__(self) -> str:
        return f"{self.name}"


class EmployeeTask(models.Model):
    AUTO_PASS = False
    STATUS_CHOICES = [
        ('новое', 'Новое'),
        ('в процессе', 'В процессе'),
        ('завершено', 'Завершено'),
        ('просрочено', 'Просрочено'),
        ('отменено', 'Отмен')
    ]

    PRIORITY_CHOICES = [
        ('низкий', 'низкий'),
        ('средний', 'средний'),
        ('высокий', 'высокий'),
    ]
    position = models.CharField(max_length=255, choices=POSITION_CHOICES, verbose_name="Должность", null=True,
                                blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник", null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задача")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано в", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено в", blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, verbose_name="Статус", default='новое')
    deadline = models.DateTimeField(verbose_name="Дедлайн")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, verbose_name="Приоритет", default='низкий')
    checked = models.BooleanField(verbose_name="Проверено")
    rating = models.IntegerField(verbose_name="Оценка", blank=True, null=True)
    address = models.CharField(max_length=255, verbose_name="Адрес", null=True, blank=True)
    comment = models.TextField(verbose_name="Комментарий", null=True, blank=True)
    autopass = models.BooleanField(verbose_name="Автопередача", default=False)

    class Meta:
        verbose_name = 'задачу сотрудника'
        verbose_name_plural = 'Задачи сотрудников'
        unique_together = ('employee', 'task')

    def __str__(self) -> str:
        return f"{self.employee} | {self.task}"

    def save(self, *args, **kwargs):

        self.assign_next_employee()
        # if self.checked:
        #     if self.status == 'завершено':
        #         self.assign_next_employee()
        #     else:
        #         pass
        if self.position is None:
            self.position = self.employee.position
        if self.rating and self.checked:
            self.employee.rating += self.rating
            self.employee.save()
        super().save(*args, **kwargs)

    def assign_next_employee(self):
        current_position = self.position
        if current_position not in WORKFLOW_ORDER:
            return
        is_saved = False
        next_position_index = WORKFLOW_ORDER.index(current_position)
        logging.info(f"Current position: {current_position}")
        logging.info(f"Next position index: {next_position_index}")
        ## if first position then it logic for copywriter
        ## else for other copywriter
        # copywiter logic position is copywriter and status is "завершено" and checked is True
        if next_position_index != 0 and self.status == 'завершено' and self.checked:
            logging.info(f"not Copier: {next_position_index}")
            next_position_index += 1
            logging.info(f"Next position: {next_position_index}")
            ## next position pick some employee
            is_saved = True
        # copywriter logic position is copywriter and status is "новое"

        if next_position_index == 0 and self.status == 'новое':
            logging.info(f"Copier: {next_position_index}")
            is_saved = True
        logging.info(
            f"assign to some copier by employee.rating and status {self.employee} | {self.task} | {self.status}")
        # employee save the task or copier with status "новое"
        # check if task is edited by employee
        logging.info(f"Auto pass: {self.AUTO_PASS}")
        if self.AUTO_PASS:
            is_saved = False
        if is_saved:
            logging.info(f"EployeeTask: {self.employee} | {self.task} | {self.status} ")
            employee_queryset = Employee.objects.filter(
                position=WORKFLOW_ORDER[next_position_index],
                status=True
            ).annotate(
                task_count=Count('employeetask')
            ).order_by('-rating', 'task_count', 'status')

            if employee_queryset.exists():
                logging.info(f'next_employee_queryset {employee_queryset}')
                highest_rating = employee_queryset.first().rating
                top_employees = employee_queryset.filter(rating=highest_rating)
                status = employee_queryset.first().status
                top_employees_status = top_employees.filter(status=status)
                employee = random.choice(
                    top_employees_status) if top_employees_status.count() > 1 else employee_queryset.first()
                logging.info(f"Employee: {employee.name}")
                EmployeeTask.objects.create(
                    employee=employee,
                    task=self.task,
                    status=self.STATUS_CHOICES[0][0],
                    deadline=self.deadline,
                    priority=self.priority,
                    checked=False,
                    rating=self.rating,
                    position=None
                )

                ## add rating to employee

                TaskHistory.objects.create(
                    employee=employee,
                    task=self.task
                )
                message = "У вас новая задача"

                Notification.objects.create(
                    employee=employee,
                    task=self.task,
                    message=message
                )


class Notification(models.Model):
    STATUS_CHOICES = [
        # ('новое', 'Новое'),
        # ('прочитано', 'Прочитано'),
        ('отправлено', 'Отправлено')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задача", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано в", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено в", blank=True, null=True)
    message = models.TextField(verbose_name="Сообщение")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="Статус", default='отправлено')

    # checked = models.BooleanField(verbose_name="Проверено")

    class Meta:
        verbose_name = 'оповещение'
        verbose_name_plural = 'Оповещения'

    def __str__(self) -> str:
        return f"{self.message}"


class TaskHistory(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задача")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано в", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено в", blank=True, null=True)

    class Meta:
        verbose_name = 'историю заданий'
        verbose_name_plural = 'История заданий'
        # unique_together = ('employee', 'task')

    def __str__(self) -> str:
        return f"{self.employee} | {self.task}"


class Balance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник", unique=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано в")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено в")
    balance = models.IntegerField(verbose_name="Баланс", default=0)
    is_approved = models.BooleanField(verbose_name="Подтверждение", default=False)

    class Meta:
        verbose_name = 'баланс сотрудника'
        verbose_name_plural = 'Баланс сотрудников'

    def __str__(self) -> str:
        return f"{self.employee} | {self.balance}"

    ## Переопределение метода save для модели Balance после потверждения баланса
    def save(self, *args, **kwargs):
        if self.is_approved:
            balance_amount = self.balance
            self.balance = 0
            self.is_approved = False
            WithdrawDeposit.objects.create(balance=self, amount=balance_amount, status='подтверждено', type='снятие')
        super().save(*args, **kwargs)


class WithdrawDeposit(models.Model):
    STATUS_CHOICES = [
        ('новое', 'Новое'),
        ('подтверждено', 'Подтверждено'),
    ]

    BALANCE_CHOICES = [
        ('снятие', 'Снятие'),
        ('пополнение', 'Пополнение'),
    ]

    balance = models.ForeignKey(Balance, on_delete=models.CASCADE, verbose_name="Баланс")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задача", blank=True, null=True)
    amount = models.IntegerField(verbose_name="Сумма")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, verbose_name="Статус")
    type = models.CharField(max_length=10, choices=BALANCE_CHOICES, verbose_name="Тип транзакции")
    comment = models.TextField(verbose_name="Описание", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано в", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено в", blank=True, null=True)

    ## todo: переопределить метод save для модели WithdrawDeposit
    # def save(self, *args, **kwargs):
    #     if self.pk is None:
    #         if self.type == 'снятие' and self.balnce.is_approved:
    #             self.balance.balance -= self.amount
    #         elif self.type == 'пополнение':
    #             self.balance.balance += self.amount
    #         self.balance.save()
    #     else:
    #         original = WithdrawDeposit.objects.get(pk=self.pk)
    #         if original.type == 'снятие' and self.balance.is_approved:
    #             self.balance.balance += original.amount
    #         elif original.type == 'пополнение':
    #             self.balance.balance -= original.amount
    #
    #         if self.type == 'снятие' and self.balance.is_approved:
    #             self.balance.balance -= self.amount
    #         elif self.type == 'пополнение':
    #             self.balance.balance += self.amount
    #
    #         self.balance.save()
    #     super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'транзакцию'
        verbose_name_plural = 'Транзакции'

    def __str__(self) -> str:
        return f"{self.balance} | {self.amount}"
