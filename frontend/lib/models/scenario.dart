import 'package:flutter/material.dart';

enum ScenarioType {
  whiteBackground,
  professionalStudio,
  modernStore,
  urbanLifestyle,
}

class Scenario {
  final ScenarioType type;
  final String label;
  final String description;
  final IconData icon;
  final String apiValue;

  const Scenario({
    required this.type,
    required this.label,
    required this.description,
    required this.icon,
    required this.apiValue,
  });

  static const List<Scenario> all = [
    Scenario(
      type: ScenarioType.whiteBackground,
      label: 'Fundo Branco',
      description: 'Clássico e-commerce',
      icon: Icons.square_outlined,
      apiValue: 'white_background',
    ),
    Scenario(
      type: ScenarioType.professionalStudio,
      label: 'Estúdio Pro',
      description: 'Iluminação dramática',
      icon: Icons.camera_enhance,
      apiValue: 'professional_studio',
    ),
    Scenario(
      type: ScenarioType.modernStore,
      label: 'Loja Moderna',
      description: 'Ambiente boutique',
      icon: Icons.store,
      apiValue: 'modern_store',
    ),
    Scenario(
      type: ScenarioType.urbanLifestyle,
      label: 'Lifestyle Urbano',
      description: 'Estilo de rua',
      icon: Icons.location_city,
      apiValue: 'urban_lifestyle',
    ),
  ];
}
