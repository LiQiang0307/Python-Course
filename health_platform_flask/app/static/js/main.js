/**
 * 前端交互脚本
 * 1) 添加记录页：根据记录类型切换显示对应字段
 * 2) 评测页：血压成对校验提示（可选增强）
 */
document.addEventListener('DOMContentLoaded', () => {
    const typeSelect = document.getElementById('record_type');
    if (typeSelect) {
        const toggle = () => {
            document.querySelectorAll('[data-record-type]').forEach(el => {
                const types = el.dataset.recordType.split(',');
                el.style.display = types.includes(typeSelect.value) ? '' : 'none';
            });
        };
        typeSelect.addEventListener('change', toggle);
        toggle();
    }
});
