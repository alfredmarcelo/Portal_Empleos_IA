import L from 'leaflet';

const Cordenadas_metro = {
    Mama_Tingo: {
        lat: 18.54683677584288,
        lng: -69.90132647494613
    },
    Juan_Pablo_Duarte: {
        lat: 18.481672336845858,
        lng: -69.91465895257345
    },
    Maria_Montez: {
        lat: 18.47887637167451,
        lng: -69.96830814754759
    },
    Centro_de_los_Heroes: {
        lat: 18.45121384737986,
        lng: -69.927740447548
    },
    Francisco_Alberto_Camaño: {
        lat: 18.45576084638658,
        lng: -69.92400614567393
    },
    Amin_Abel: {
        lat: 18.4594398190675,
        lng: -69.91654160519663
    },
    Joaquin_balaguer: {
        lat: 18.464716359775906,
        lng: -69.90995404567386
    },
    Casandra_Damiron: {
        lat: 18.4714276242592,
        lng: -69.9119764014945
    },
    Juan_Bosh: {
        lat: 18.476943022498716,
        lng: -69.91386477450956
    },
    Manuel_arturo_Peña_battle: {
        lat: 18.486102533070724,
        lng: -69.91438798985254
    },
    Pedro_livio_cedeño: {
        lat: 18.49357962891722,
        lng: -69.9149108456732
    },
    Los_tainos: {
        lat: 18.49982927109022,
        lng: -69.9154472186883
    },
    Maximo_gomez: {
        lat: 18.507693387773603,
        lng: -69.9158964898523
    },
    Hermanas_mirabal: {
        lat: 18.518282229137203,
        lng: -69.91519512053888
    },
    Jose_francisco_peña_gomez: {
        lat: 18.525652967466876,
        lng: -69.91640130149337
    },
    Gregorio_luperon: {
        lat: 18.530029770972618,
        lng: -69.90861664567248
    }
}

export default function Calcular_distancia_metro(destino) {

    for (const [key, value] of Object.entries(Cordenadas_metro)) {
        const metro = L.latLng(value.lat, value.lng);
        const empleo = L.latLng(destino.lat, destino.lng);

        const distancia = metro.distanceTo(empleo);
        if (distancia <= 800) {
            return key;
        }
    }
    return 'No hay metro cercano';
}