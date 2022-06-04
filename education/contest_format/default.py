from datetime import timedelta
from django.utils.translation import gettext_lazy
from django.db.models import Max
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.template.defaultfilters import floatformat

from .base import BaseContestFormat
from .registry import registry_contest_format

from backend.utils.timedelta import nice_repr

@registry_contest_format('default')
class DefaultContestFormat(BaseContestFormat):
    name = gettext_lazy('Default')

    def __init__(self, contest):
        super().__init__(contest)
    
    def update_participation(self, participation):
        cumtime = 0
        format_data = {}

        max_points = 0
        problems = participation.contest.contest_problems.all()
        for problem in problems:
            max_points += problem.points
        
        for submission in participation.submissions.all():
            if submission.max_points != max_points:
                submission.judge()

        sub = participation.submissions.aggregate(point=Max('points'))

        submission = participation.submissions.filter(points=sub['point']).order_by('date').first()

        # print(sub)


        dt = (submission.date - participation.start).total_seconds()
        cumtime += dt
        
        for sub_problem in submission.problems.all():
            # print(sub_problem.problem.id)
            format_data[str(sub_problem.problem.id)] = {'status': sub_problem.result}
        
        participation.cumtime = max(cumtime, 0)
        participation.score = round(submission.points * 100 / max_points, self.contest.points_precision)
        participation.tiebreaker = 0
        participation.format_data = format_data

        # print(format_data)
        
        participation.save()
    
    def display_user_problem(self, participation, contest_problem):
        # print('display_user_problem')
        format_data = (participation.format_data or {}).get(str(contest_problem.id))

        # print('display_user_problem: %s', str(contest_problem.problem.id))

        if format_data:
            return format_html(
                u'<td class="problem_cell text-white {state}"><div class="my-auto flex items-center justify-center"><span class="material-icons">{result}</span></div></td>',
                state='bg-green-500' if format_data['status'] else 'bg-red-500',
                result='done' if format_data['status'] else 'close'
            )
        else:
            return mark_safe('<td class="problem_cell"></td>')
    
    def display_participation_result(self, participation):
        # print("display_result ",participation.virtual, participation.score)
        return format_html(
            u'<td class="py-1 px-3 text-center"><div class="flex flex-col items-center"> \
                <div class="font-bold">{points}</div><div class="text-gray-500 text-xs">{cumtime}</div></div></td>',
            points=floatformat(participation.score, -self.contest.points_precision),
            cumtime=nice_repr(timedelta(seconds=participation.cumtime), 'noday'),
        )

    def get_problem_breakdown(self, participation, contest_problems):
        return [(participation.format_data or {}).get(str(contest_problem.id)) for contest_problem in contest_problems]

    def get_label_for_problem(self, index):
        return str(index + 1)