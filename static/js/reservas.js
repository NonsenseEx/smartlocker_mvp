(function () {
  "use strict";

  var dataNode = document.getElementById("sl-calendario-data");
  if (!dataNode) return;

  var data;
  try {
    data = JSON.parse(dataNode.textContent);
  } catch (error) {
    return;
  }

  var dias = data.dias || {};
  var meses = data.meses || [];
  var indiceMes = 0;
  var fechaSeleccionada = null;
  var bloqueSeleccionado = null;

  var grid = document.getElementById("slCalendarGrid");
  var titulo = document.getElementById("slMesTitulo");
  var anterior = document.getElementById("slMesAnterior");
  var siguiente = document.getElementById("slMesSiguiente");
  var slotsList = document.getElementById("slSlotsList");
  var resumenFecha = document.getElementById("slResumenFecha");
  var resumenHora = document.getElementById("slResumenHora");
  var hiddenFecha = document.getElementById("id_fecha_reserva");
  var hiddenBloque = document.getElementById("id_bloque_horario");
  var cantidad = document.getElementById("id_cantidad");
  var cantidadValor = document.getElementById("slCantidadValor");
  var cantidadDetalle = document.getElementById("slCantidadDetalle");
  var cantidadMax = document.getElementById("slCantidadMax");
  var menos = document.getElementById("slCantidadMenos");
  var mas = document.getElementById("slCantidadMas");
  var submit = document.getElementById("slSubmitReserva");

  if (!grid || !meses.length) {
    if (titulo) titulo.textContent = "Sin fechas disponibles";
    if (anterior) anterior.disabled = true;
    if (siguiente) siguiente.disabled = true;
    return;
  }

  function pad(numero) {
    return String(numero).padStart(2, "0");
  }

  function clave(anio, mes, dia) {
    return anio + "-" + pad(mes) + "-" + pad(dia);
  }

  function textoFecha(claveFecha) {
    var info = dias[claveFecha];
    if (!info) return claveFecha;
    return info.numero + " de " + info.mes + " de " + info.anio + " (" + info.dia + ")";
  }

  function renderMes() {
    var mes = meses[indiceMes];
    titulo.textContent = mes.label;
    grid.innerHTML = "";

    var desplazamiento = (new Date(mes.anio, mes.mes - 1, 1).getDay() + 6) % 7;
    var totalDias = new Date(mes.anio, mes.mes, 0).getDate();
    var i;

    for (i = 0; i < desplazamiento; i++) {
      var vacio = document.createElement("span");
      vacio.className = "sl-calendar-day is-empty";
      grid.appendChild(vacio);
    }

    for (var dia = 1; dia <= totalDias; dia++) {
      var key = clave(mes.anio, mes.mes, dia);
      var info = dias[key];
      var boton = document.createElement("button");
      boton.type = "button";
      boton.className = "sl-calendar-day";
      boton.textContent = dia;

      if (!info) {
        boton.classList.add("is-off");
        boton.disabled = true;
        boton.setAttribute("aria-label", dia + " — no laborable o fuera de plazo");
      } else if (!info.hay_horas) {
        boton.classList.add("is-full");
        boton.disabled = true;
        boton.setAttribute("aria-label", info.dia + " " + dia + " — sin cupo");
      } else {
        boton.classList.add("is-free");
        boton.setAttribute("aria-label", info.dia + " " + dia + " — con horas libres");
        boton.addEventListener("click", function () {
          seleccionarFecha(this.dataset.fecha);
        });
      }

      boton.dataset.fecha = key;
      if (key === data.hoy) boton.classList.add("is-today");
      if (key === fechaSeleccionada) boton.classList.add("is-selected");
      grid.appendChild(boton);
    }

    anterior.disabled = indiceMes === 0;
    siguiente.disabled = indiceMes === meses.length - 1;
  }

  function resetCantidad() {
    cantidad.value = 1;
    cantidad.max = 1;
    cantidad.disabled = true;
    cantidadValor.textContent = "—";
    cantidadDetalle.textContent = "Elige un horario para activar el selector.";
    cantidadMax.textContent = "—";
    menos.disabled = true;
    mas.disabled = true;
    submit.disabled = true;
    actualizarBarra();
  }

  function renderSlots() {
    slotsList.innerHTML = "";
    var info = dias[fechaSeleccionada];
    if (!info) return;

    info.slots.forEach(function (slot) {
      var boton = document.createElement("button");
      boton.type = "button";
      boton.className = "sl-slot" + (slot.disponible ? "" : " is-full");
      boton.disabled = !slot.disponible;
      boton.dataset.bloque = slot.bloque;
      boton.dataset.hora = slot.hora;
      boton.dataset.libres = slot.libres;

      var hora = document.createElement("span");
      hora.className = "sl-slot-time";
      hora.textContent = slot.hora;

      var cupo = document.createElement("span");
      cupo.className = "sl-slot-stock";
      cupo.textContent = slot.disponible ? slot.libres + " libres" : "Sin cupo";

      boton.appendChild(hora);
      boton.appendChild(cupo);
      boton.addEventListener("click", function () {
        seleccionarHorario(boton);
      });
      slotsList.appendChild(boton);
    });
  }

  function seleccionarFecha(key) {
    fechaSeleccionada = key;
    bloqueSeleccionado = null;
    hiddenFecha.value = key;
    hiddenBloque.value = "";
    resumenFecha.textContent = textoFecha(key);
    resumenHora.textContent = "Elige un horario";
    renderMes();
    renderSlots();
    resetCantidad();
  }

  function seleccionarHorario(boton) {
    bloqueSeleccionado = boton.dataset.bloque;
    hiddenBloque.value = bloqueSeleccionado;
    resumenHora.textContent = boton.dataset.hora;

    slotsList.querySelectorAll(".sl-slot").forEach(function (item) {
      item.classList.toggle("is-active", item === boton);
    });

    var max = Math.min(data.stock, parseInt(boton.dataset.libres, 10));
    cantidad.min = 1;
    cantidad.max = max;
    cantidad.value = 1;
    cantidad.disabled = false;
    cantidadMax.textContent = max;
    cantidadDetalle.textContent = "Máximo " + max + " unidad(es) en este horario.";
    submit.disabled = false;
    actualizarBarra();
  }

  function actualizarBarra() {
    var min = parseInt(cantidad.min, 10) || 1;
    var max = parseInt(cantidad.max, 10) || 1;
    var valor = parseInt(cantidad.value, 10) || min;
    var pct = max > min ? ((valor - min) / (max - min)) * 100 : 0;
    cantidad.style.setProperty("--pct", pct + "%");
    cantidadValor.textContent = cantidad.disabled ? "—" : valor + (valor === 1 ? " unidad" : " unidades");
    menos.disabled = cantidad.disabled || valor <= min;
    mas.disabled = cantidad.disabled || valor >= max;
  }

  anterior.addEventListener("click", function () {
    if (indiceMes > 0) {
      indiceMes--;
      renderMes();
    }
  });

  siguiente.addEventListener("click", function () {
    if (indiceMes < meses.length - 1) {
      indiceMes++;
      renderMes();
    }
  });

  cantidad.addEventListener("input", actualizarBarra);
  menos.addEventListener("click", function () {
    cantidad.value = Math.max(parseInt(cantidad.min, 10), parseInt(cantidad.value, 10) - 1);
    actualizarBarra();
  });
  mas.addEventListener("click", function () {
    cantidad.value = Math.min(parseInt(cantidad.max, 10), parseInt(cantidad.value, 10) + 1);
    actualizarBarra();
  });

  document.getElementById("slReservaForm").addEventListener("submit", function (event) {
    if (!fechaSeleccionada || !bloqueSeleccionado) {
      event.preventDefault();
    }
  });

  resetCantidad();
  renderMes();
})();
