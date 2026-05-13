// Fitness Food - main.js
function togglePass(id, btn) {
    const inp = document.getElementById(id);
    inp.type = inp.type === 'password' ? 'text' : 'password';
    btn.textContent = inp.type === 'password' ? '👁' : '🙈';
}
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('editar-btn')) {
        const d = e.target.dataset;
        document.getElementById('formEditar').action = `/editar-usuario/${d.id}`;
        document.getElementById('editRol').value = d.rol;
        document.getElementById('editObjetivo').value = d.objetivo;
        document.getElementById('editActivo').value = d.activo;
        new bootstrap.Modal(document.getElementById('modalEditar')).show();
    }
});
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('eliminar-registro-btn')) {
        const id = e.target.dataset.id;
        if (confirm('¿Eliminar este registro?')) {
            fetch(`/registro/${id}`, { method: 'DELETE' })
                .then(res => {
                    if (res.ok) e.target.closest('tr').remove();
                    else alert('Error al eliminar el registro.');
                });
        }
    }
});