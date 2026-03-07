$(document).ready(function() {      
    CreateTooltip();
    AgregarAyudaAElementoSoloTexto('id', 'texto', 'ayuda');
}); 

function goBack(){
    if (window.history.length == 1){
        window.close();
    }
    window.history.back();
}

setTimeout(function () {
    $('#alert').alert('close');
}, 5000);

function AgregarAyudaAElementoSoloTexto(id_elemento, texto, ayuda, permite ){
    
    if(permite){
        $('#'+id_elemento).after('<span class="badge aviso_vulnerabilidad_badge" style="background-color:#329ef4"data-bs-toggle="tooltip"  data-bs-original-title="' + ayuda + '" ><i class="fa fa-check" ></i>' + texto + '<i class="fa fa-info-circle aviso_vulnerabilidad_info"></i></span>');
    }else{
        $('#'+id_elemento).after('<span class="badge aviso_vulnerabilidad_badge" style="background-color:#329ef4"data-bs-toggle="tooltip"  data-bs-original-title="' + ayuda + '" ><i class="fa fa-times" ></i>'+ texto + '<i class="fa fa-info-circle aviso_vulnerabilidad_info"></i></span>');    
    }    
}   

function CreateTooltip() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    })
}
