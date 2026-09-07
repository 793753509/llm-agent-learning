"""只保留课程中用到的三种流程错误。"""


class AgentError(Exception):
    """Agent 错误的共同父类。"""


class EmptyQuestionError(AgentError):
    pass


class InvalidModelReplyError(AgentError):
    pass


class MaxStepsExceededError(AgentError):
    pass
