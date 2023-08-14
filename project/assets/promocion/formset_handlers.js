
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


    $(document).ready(function() {
        // Escuchar el clic en el botón "Agregar otro"
        $(document).on("click", ".add-row a", function() {
          // Esperar un breve momento para asegurarnos de que el nuevo componente se haya agregado
          setTimeout(function() {
            // Obtener el índice del nuevo componente agregado
            var newIndex = $(".dynamic-tabular.inline-group").find(".form-row").length - 1;
      
            // Construir el ID del nuevo componente
            var newComponentId = "#id_libro_set-" + newIndex + "-titulo";
      
            // Acceder al componente y obtener su ID
            var idDelNuevoComponente = $(newComponentId).attr("id");
      
            console.log("ID del nuevo componente:", idDelNuevoComponente);
          }, 100); // Ajustar este tiempo según sea necesario
        });
      });









});