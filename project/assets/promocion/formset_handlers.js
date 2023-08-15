
/*
//no inicia chequeado. asi que desativamos el campo de precio
if (!jQuery("#id_es_por_precio").is(":checked")) {
    jQuery("#id_promocionarticulo_set-0-valor").val(valor)
    jQuery("#id_promocionarticulo_set-0-valor").prop("disabled", true);
}
*/

//evento asociado al check
/*
jQuery("#id_es_por_precio").click(function (event) {
    if (jQuery("#id_es_por_precio").is(":checked")) {
        //jQuery("#id_promocionarticulo_set-0-valor").val(null)
        jQuery("#id_promocionarticulo_set-0-valor").prop("disabled", false);
    } else {
        //let valor= parseFloat(0.00);
        //console.log(valor);
        //jQuery("#id_promocionarticulo_set-0-valor").val(valor)
        jQuery("#id_promocionarticulo_set-0-valor").prop("disabled", true);
    }
}); 
*/
/*
jQuery(document).ready(function () {
    let newComponentId = null
    // Escuchar el clic en el botón "Agregar otro"
    jQuery(document).on("click", ".add-row a", function () {
        // Esperar un breve momento para asegurarnos de que el nuevo componente se haya agregado
        setTimeout(function () {
            // Obtener el índice del nuevo componente agregado
            var newIndex = jQuery(".js-inline-admin-formset").find(".form-row").length - 2;
            console.log('nuevo index');
            console.log(newIndex);
            // Construir el ID del nuevo componente
            newComponentId = "#id_promocionarticulo_set-" + newIndex + "-valor";
            console.log(newComponentId)
            // Acceder al componente y obtener su ID
            var idDelNuevoComponente = jQuery(newComponentId).attr("id");

            console.log("ID del nuevo componente:", idDelNuevoComponente);
            //ahora ya con el componente obtenido vemos si lo habilitamos o no
            if (jQuery("#id_es_por_precio").is(":checked")) {
                jQuery(newComponentId).val(null)
                jQuery(newComponentId).prop("disabled", false);
            } else {
                jQuery(newComponentId).val(valor)
                jQuery(newComponentId).prop("disabled", true);
            }
        }, 100); // Ajustar este tiempo según sea necesario

    });
});

*/