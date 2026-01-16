
import 'leaflet/dist/leaflet.css';
import { useEffect, useState } from 'react';
import './Styles/Apple_map.css';
import { FaWalking, FaCar, FaMotorcycle } from "react-icons/fa";
import Calcular_distancia_metro from './Calcular_distancia_metro';
import Mapa from './Mapa';

const TIPOSRUTA = {
    PIE: 'walking',
    AUTO: 'driving',
    MOTOCICLETA: 'cycling'
}

export default function Apple_map() {
    const [ruta, setRuta] = useState([]);
    const [minutos, setMinutos] = useState(0);
    const [distancia, setDistancia] = useState(0);
    const [tiporuta, setTiporuta] = useState(TIPOSRUTA.AUTO);
    const [position, setPosition] = useState({
        lat: 0,
        lng: 0
    });
    const [destino, setDestino] = useState({
        lat: 18.473518729117163,
        lng: -69.83797413637272
    });

    useEffect(() => {
        navigator.geolocation.getCurrentPosition((position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            setPosition({ lat, lng });
        });
    }, []);

    async function obtenerRutaAPie() {
        const url =
            `https://router.project-osrm.org/route/v1/${tiporuta}/` +
            `${position.lng},${position.lat};` +
            `${destino.lng},${destino.lat}` +
            '?overview=full&geometries=geojson';

        const res = await fetch(url);
        const data = await res.json();
        const minutos = Math.round(data.routes[0].duration / 60);
        const dist = (data.routes[0].distance / 1000).toFixed(1);

        setMinutos(minutos);
        setDistancia(dist);
        return data.routes[0].geometry.coordinates;
    }

    useEffect(() => {
        obtenerRutaAPie().then(coords => {
            // OSRM → [lng, lat]
            setRuta(coords.map(c => [c[1], c[0]]));
        });
    }, [tiporuta, position]);

    return (
        <div id="Job-Search-Frame2">
            <div id="Map-Container">
                <Mapa ruta={ruta} destino={destino} position={position} />
                <div id="Buttons-Container">
                    <div id='Button' onClick={() => setTiporuta(TIPOSRUTA.PIE)} style={{ backgroundColor: tiporuta === 'walking' ? 'grey' : 'var(--job-frame-bg)', borderTopLeftRadius: 10 }}>
                        <FaWalking size={18} style={{ marginRight: 5 }} />
                    </div>
                    <div id='Button' onClick={() => setTiporuta(TIPOSRUTA.AUTO)} style={{ backgroundColor: tiporuta === 'driving' ? 'grey' : 'var(--job-frame-bg)' }}>
                        <FaCar size={18} style={{ marginRight: 5 }} />
                    </div>
                    <div id='Button' onClick={() => setTiporuta(TIPOSRUTA.MOTOCICLETA)} style={{ backgroundColor: tiporuta === 'cycling' ? 'grey' : 'var(--job-frame-bg)', borderTopRightRadius: 10 }}>
                        <FaMotorcycle size={18} style={{ marginRight: 5 }} />
                    </div>
                </div>
            </div>
            <div id="Info-Container">
                <div className="Info-Box">
                    <p>Tiempo Estimado</p>
                    <h3>{minutos} min</h3>
                </div>
                <div className="Info-Box">
                    <p>Distancia</p>
                    <h3>{distancia} km</h3>
                </div>
                <div className="Info-Box">
                    <p>Metro cercano</p>
                    <h3>{Calcular_distancia_metro(destino).replaceAll('_', ' ')}</h3>
                </div>
            </div>
        </div >
    );
}
