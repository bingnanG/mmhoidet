# model settings
model = dict(
    type='QPIC',
    backbone=dict(
        type='ResNet',
        depth=50,
        num_stages=4,
        out_indices=(3,),
        frozen_stages=1,
        norm_cfg=dict(type='BN', requires_grad=False),
        norm_eval=True,
        style='pytorch',
        init_cfg=dict(type='Pretrained', checkpoint='torchvision://resnet50')),
    hoi_head=dict(
        type='QPICHead',
        num_obj_classes=80,
        num_verb_classes=117,
        in_channels=2048,
        num_query=100,
        num_reg_cls=2,
        sync_cls_avg_factor=False,
        transformer=dict(
            type='Transformer',
            encoder=dict(
                type='DetrTransformerEncoder',
                num_layers=6,
                transformerlayers=dict(
                    type='BaseTransformerLayer',
                    attn_cfgs=[
                        dict(
                            type='MultiheadAttention',
                            embed_dims=256,
                            num_heads=8,
                            dropout=0.1)
                    ],
                    feedforward_channels=2048,
                    ffn_dropout=0.1,
                    operation_order=('self_attn', 'norm', 'ffn', 'norm'))),
            decoder=dict(
                type='DetrTransformerDecoder',
                return_intermediate=True,
                num_layers=6,
                transformerlayers=dict(
                    type='DetrTransformerDecoderLayer',
                    attn_cfgs=dict(
                        type='MultiheadAttention',
                        embed_dims=256,
                        num_heads=8,
                        dropout=0.1),
                    feedforward_channels=2048,
                    ffn_dropout=0.1,
                    operation_order=('self_attn', 'norm', 'cross_attn', 'norm',
                                     'ffn', 'norm')),
            )),
        positional_encoding=dict(
            type='SinePositionalEncoding', num_feats=128, normalize=True),
        loss_obj_cls=dict(type='CrossEntropyLoss',
                          bg_cls_weight=0.1,
                          use_sigmoid=False,
                          loss_weight=1.0,
                          class_weight=1.0),
        loss_verb_cls=dict(
            type='ElementWiseFocalLoss',
            use_sigmoid=True,
            loss_weight=1.0),
        loss_bbox=dict(type='L1Loss', loss_weight=5.0),
        loss_iou=dict(type='GIoULoss', loss_weight=2.0)),

    train_cfg=dict(
        assigner=dict(
            type='HungarianAssigner',
            obj_cls_cost=dict(type='ClsSoftmaxCost', weight=1.),
            verb_cls_cost=dict(type='ClsNoSoftmaxCost', weight=1.),
            reg_cost=dict(type='MaxBBoxL1Cost', weight=5.0, box_format='xywh'),
            iou_cost=dict(type='MaxIoUCost', iou_mode='giou', weight=2.0))),
    test_cfg=dict(max_per_img=100))

# dataset settings
dataset_type = 'HICODet'
data_root = 'data/hico_20160224_det/'
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)
# train_pipeline, NOTE the img_scale and the Pad's size_divisor is different
# from the default setting in mmdet.
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations'),
    dict(type='RandomFlip', flip_ratio=0.5),  # TODO: 暂时先不使用
    dict(
        type='AutoAugment',
        policies=[
            [
                dict(
                    type='Resize',
                    img_scale=[(480, 1333), (512, 1333), (544, 1333), (576, 1333),
                               (608, 1333), (640, 1333), (672, 1333), (704, 1333),
                               (736, 1333), (768, 1333), (800, 1333)],
                    multiscale_mode='value',
                    keep_ratio=True)
            ],
            [
                dict(
                    type='Resize',
                    img_scale=[(400, 1333), (500, 1333), (600, 1333)],
                    multiscale_mode='value',
                    keep_ratio=True),
                dict(
                    type='RandomCrop',
                    crop_type='absolute_range',
                    crop_size=(384, 600),
                    allow_negative_crop=True),  # Whether to allow a crop that dose not contain any bbox area.
                dict(
                    type='Resize',
                    img_scale=[(480, 1333), (512, 1333), (544, 1333),
                               (576, 1333), (608, 1333), (640, 1333),
                               (672, 1333), (704, 1333), (736, 1333),
                               (768, 1333), (800, 1333)],
                    multiscale_mode='value',
                    override=True,
                    keep_ratio=True)
            ]]),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=1),  # No padding here.
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_sub_bboxes', 'gt_obj_bboxes', 'gt_obj_labels', 'gt_verb_labels'])
]
# test_pipeline, NOTE the Pad's size_divisor is different from the default
# setting (size_divisor=32). While there is little effect on the performance
# whether we use the default setting or use size_divisor=1.
test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(1333, 800),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='Pad', size_divisor=1),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img'])
        ])
]

data = dict(
    samples_per_gpu=4,
    workers_per_gpu=4,
    train=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/trainval_hico.json',
        img_prefix=data_root + 'images/train2015/',
        valid_hois_file=data_root + 'annotations/corre_hico.npy',
        pipeline=train_pipeline,
        mode='train'),
    val=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/test_hico.json',
        img_prefix=data_root + 'images/test2015/',
        valid_hois_file=data_root + 'annotations/corre_hico.npy',
        pipeline=test_pipeline,
        mode='val'),
    test=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/test_hico.json',
        img_prefix=data_root + 'images/test2015/',
        valid_hois_file=data_root + 'annotations/corre_hico.npy',
        pipeline=test_pipeline,
        mode='test'))  # todo：最好在外部也可以引入进行设置

evaluation = dict(interval=100, metric='mAP')

# optimizer
optimizer = dict(
    type='AdamW',
    lr=0.0001,
    weight_decay=0.0001,
    paramwise_cfg=dict(
        custom_keys={'backbone': dict(lr_mult=0.1, decay_mult=1.0)}))
optimizer_config = dict(grad_clip=dict(max_norm=0.1, norm_type=2))

# learning policy
"""
 Args:
    step (int | list[int]): Step to decay the LR. If an int value is given,
    regard it as the decay interval. If a list is given, decay LR at
    these steps.
"""
lr_config = dict(policy='step', step=[150])
runner = dict(type='EpochBasedRunner', max_epochs=600)

# setting runtime
checkpoint_config = dict(interval=1)  # -1 means never
# yapf:disable
log_config = dict(
    interval=50,
    hooks=[
        dict(type='TextLoggerHook'),
        dict(type='TensorboardLoggerHook')
    ])
# yapf:enable
custom_hooks = [dict(type='NumClassCheckHook')]

dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = None
resume_from = None
workflow = [('train', 1)]
resume_from = './work_dirs/qpic_r50_150e_hico/latest.pth'
# load_from = './checkpoints/detr_r50_8x2_150e_coco_20201130_194835-2c4b8974.pth'
