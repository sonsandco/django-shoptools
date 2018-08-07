from django.dispatch import Signal

create_pre_save = Signal(providing_args=['request'])
create_post_save = Signal(providing_args=['request'])
update_pre_save = Signal(providing_args=['request'])
update_post_save = Signal(providing_args=['request'])
