import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../features/trust_monitor/providers/trust_provider.dart';

class BehavioralWrapper extends StatefulWidget {
  final Widget child;
  
  const BehavioralWrapper({
    super.key,
    required this.child,
  });

  @override
  State<BehavioralWrapper> createState() => _BehavioralWrapperState();
}

class _BehavioralWrapperState extends State<BehavioralWrapper> {
  Offset? _panStartPosition;
  DateTime? _panStartTime;
  
  @override
  Widget build(BuildContext context) {
    return Consumer<TrustProvider>(
      builder: (context, trustProvider, child) {
        return GestureDetector(
          onTapDown: (details) {
            _recordTap(context, details, trustProvider);
          },
          onPanStart: (details) {
            _recordPanStart(details);
          },
          onPanUpdate: (details) {
            _recordPanUpdate(details, trustProvider);
          },
          onPanEnd: (details) {
            _recordPanEnd(details, trustProvider);
          },
          child: widget.child,
        );
      },
    );
  }
  
  void _recordTap(BuildContext context, TapDownDetails details, TrustProvider trustProvider) {
    final position = details.localPosition;
    final pressure = 1.0; // Default pressure for web platform
    
    trustProvider.recordTap(position.dx, position.dy, pressure);
  }
  
  void _recordPanStart(DragStartDetails details) {
    _panStartPosition = details.localPosition;
    _panStartTime = DateTime.now();
  }
  
  void _recordPanUpdate(DragUpdateDetails details, TrustProvider trustProvider) {
    // Record continuous swipe movement if needed
  }
  
  void _recordPanEnd(DragEndDetails details, TrustProvider trustProvider) {
    if (_panStartPosition != null && _panStartTime != null) {
      final endPosition = details.localPosition;
      final velocity = details.velocity.pixelsPerSecond.distance;
      
      trustProvider.recordSwipe(
        _panStartPosition!.dx,
        _panStartPosition!.dy,
        endPosition.dx,
        endPosition.dy,
        velocity,
      );
      
      _panStartPosition = null;
      _panStartTime = null;
    }
  }
}