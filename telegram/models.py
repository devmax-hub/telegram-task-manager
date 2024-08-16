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
    file = models.FileField(max_length=100, blank=True, null=True, verbose_name="Файл")
    link = models.URLField(verbose_name="Ссылка", blank=True, null=True)

    class Meta:
        verbose_name = 'задачу'
        verbose_name_plural = 'Задачи'

    def __str__(self) -> str:
        return f"{self.name}"


class EmployeeTask(models.Model):
    STATUS_CHOICES = [
        ('новое', 'Новое'),
        ('в процессе', 'В процессе'),
        ('завершено', 'Завершено'),
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


    class Meta:
        verbose_name = 'задачу сотрудника'
        verbose_name_plural = 'Задачи сотрудников'
        unique_together = ('employee', 'task')

    def __str__(self) -> str:
        return f"{self.employee} | {self.task}"

    def save(self, *args, **kwargs):
        if self.position is not None:
            self.assign_employee()
        if self.checked:
            if self.status == 'завершено':
                self.assign_next_employee()
            else:
                pass
        super().save(*args, **kwargs)

    def assign_employee(self):
        current_position = self.position

        if current_position not in WORKFLOW_ORDER:
            return

        position_index = WORKFLOW_ORDER.index(current_position)

        if position_index >= len(WORKFLOW_ORDER):
            self.status = 'завершено'
            return

        position = WORKFLOW_ORDER[position_index]

        employee_queryset = Employee.objects.filter(
            position=position,
            status=True
        ).annotate(
            task_count=Count('employeetask')
        ).order_by('-rating', 'task_count') #'status'

        if not employee_queryset.exists():
            employee_queryset = Employee.objects.filter(
                position=position
            ).annotate(
                task_count=Count('employeetask')
            ).order_by('-rating', 'task_count')

        if employee_queryset.exists():
            highest_rating = employee_queryset.first().rating
            top_employees = employee_queryset.filter(rating=highest_rating)

            employee = random.choice(
                top_employees) if top_employees.count() > 1 else employee_queryset.first()

            logging.info(f"Employee: {employee.id}")

            # employee_rating = employee.rating
            # employee_rating += self.rating
            # Employee.objects.filter(id=self.employee.id).update(rating=employee_rating)

            EmployeeTask.objects.create(
                employee=employee,
                task=self.task,
                status='новое',
                deadline=self.deadline,
                priority=self.priority,
                checked=False,
                rating=self.rating
            )

            TaskHistory.objects.create(
                employee=employee,
                task=self.task
            )

            message = "У вас новая задача"
            bot.send_message(chat_id=employee.chat_id, text=message)
            Notification.objects.create(
                employee=employee,
                task=self.task,
                message=message
            )
    def assign_next_employee(self):
        current_position = self.employee.position

        if current_position not in WORKFLOW_ORDER:
            return

        next_position_index = WORKFLOW_ORDER.index(current_position)

        if next_position_index >= len(WORKFLOW_ORDER):
            self.status = 'завершено'
            return

        next_position = WORKFLOW_ORDER[next_position_index]

        next_employee_queryset = Employee.objects.filter(
            position=next_position,
            status=True
        ).annotate(
            task_count=Count('employeetask')
        ).order_by('-rating', 'task_count')

        if not next_employee_queryset.exists():
            next_employee_queryset = Employee.objects.filter(
                position=next_position
            ).annotate(
                task_count=Count('employeetask')
            ).order_by('-rating', 'task_count')

        if next_employee_queryset.exists():
            highest_rating = next_employee_queryset.first().rating
            top_employees = next_employee_queryset.filter(rating=highest_rating)

            next_employee = random.choice(
                top_employees) if top_employees.count() > 1 else next_employee_queryset.first()

            employee_rating = self.employee.rating
            employee_rating += self.rating
            Employee.objects.filter(id=self.employee.id).update(rating=employee_rating)

            EmployeeTask.objects.create(
                employee=next_employee,
                task=self.task,
                status='новое',
                deadline=self.deadline,
                priority=self.priority,
                checked=False,
                rating=self.rating
            )

            TaskHistory.objects.create(
                employee=self.employee,
                task=self.task
            )

            message = "У вас новая задача"
            bot.send_message(chat_id=next_employee.chat_id, text=message)
            Notification.objects.create(
                employee=next_employee,
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



