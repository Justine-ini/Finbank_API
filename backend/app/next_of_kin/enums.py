from enum import Enum

class RelationshipTypeEnum(str, Enum):
    Spouse = "Spouse"
    Parent = "Parent"
    Child = "Child"
    Sibling = "Sibling"
    Other = "Other"