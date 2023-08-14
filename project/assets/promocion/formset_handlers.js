
if (!jQuery("#id_es_por_precio").is(":checked")) {
    jQuery("#id_promocionarticulo_set-0-valor").val(0)
    jQuery("#id_promocionarticulo_set-0-valor").prop("disabled", true);
}


jQuery("#id_es_por_precio").click(function(event) {
    if (jQuery("#id_es_por_precio").is(":checked")) {
        jQuery("#id_promocionarticulo_set-0-valor").val(null)
        jQuery("#id_promocionarticulo_set-0-valor").prop("disabled", false);
    }else{
        jQuery("#id_promocionarticulo_set-0-valor").val(0)
        jQuery("#id_promocionarticulo_set-0-valor").prop("disabled", true);
    }
 });

 document.addEventListener('formset:added', (event) => {
    if (jQuery("#id_es_por_precio").is(":checked")) {
        jQuery("#id_promocionarticulo_set-0-valor").val(null)
        jQuery("#id_promocionarticulo_set-0-valor").prop("disabled", false);
    }else{
        jQuery("#id_promocionarticulo_set-0-valor").val(0)
        jQuery("#id_promocionarticulo_set-0-valor").prop("disabled", true);
    }

});