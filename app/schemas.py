from pydantic import BaseModel
from enum import Enum


class LabelValueItem(BaseModel):
    label: str
    value: str


class MainPageResponse(BaseModel):

    class SmallCharts(BaseModel):

        class Applications(BaseModel):
            data: list[LabelValueItem]
            range: str
            total: int
            today_online: int
            today_offlie: int

        class Average(BaseModel):
            data: list[LabelValueItem]
            range: str
            total: int

        class Approvals(BaseModel):
            all: int
            today: int

        applications: Applications
        average: Average
        approvals: Approvals

    class ApplicationsApprovalItem(BaseModel):
        class ChoicesType(Enum):
            application = 'application'
            approval = 'approval'

        type: ChoicesType
        count: int
        date: str

    small_charts: SmallCharts
    applications_approval: list[ApplicationsApprovalItem]
    average_ege: list[LabelValueItem]
    highballs: list[LabelValueItem]
    applications_by_programs: list[LabelValueItem]
