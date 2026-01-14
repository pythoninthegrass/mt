export function createNowPlayingView(Alpine) {
  Alpine.data('nowPlayingView', () => ({
    dragging: null,
    dragOverIdx: null,
    scrollInterval: null,
    dragY: 0,
    dragStartY: 0,
    dragItemHeight: 0,
    
    startDrag(idx, event) {
      event.preventDefault();
      
      const target = event.currentTarget.closest('.queue-item');
      if (!target) return;
      
      const rect = target.getBoundingClientRect();
      this.dragItemHeight = rect.height;
      this.dragStartY = rect.top;
      this.dragY = event.clientY || event.touches?.[0]?.clientY || rect.top;
      
      this.dragging = idx;
      this.dragOverIdx = null;
      
      const container = this.$refs.sortableContainer?.parentElement;
      
      const onMove = (e) => {
        const y = e.clientY || e.touches?.[0]?.clientY;
        if (y === undefined) return;
        
        this.dragY = y;
        this.handleAutoScroll(y, container);
        this.updateDropTarget(y);
      };
      
      const onEnd = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onEnd);
        document.removeEventListener('touchmove', onMove);
        document.removeEventListener('touchend', onEnd);
        
        this.stopAutoScroll();
        
        if (this.dragging !== null && this.dragOverIdx !== null && this.dragging !== this.dragOverIdx) {
          this.reorder(this.dragging, this.dragOverIdx);
        }
        
        this.dragging = null;
        this.dragOverIdx = null;
      };
      
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onEnd);
      document.addEventListener('touchmove', onMove, { passive: true });
      document.addEventListener('touchend', onEnd);
    },
    
    updateDropTarget(y) {
      const container = this.$refs.sortableContainer;
      if (!container) return;
      
      const items = container.querySelectorAll('.queue-item-wrapper');
      let newOverIdx = null;
      
      for (let i = 0; i < items.length; i++) {
        if (i === this.dragging) continue;
        
        const rect = items[i].getBoundingClientRect();
        const midY = rect.top + rect.height / 2;
        
        if (y < midY) {
          newOverIdx = i;
          break;
        }
      }
      
      if (newOverIdx === null) {
        newOverIdx = this.$store.queue.items.length;
      }
      
      if (newOverIdx > this.dragging) {
        newOverIdx = Math.min(newOverIdx, this.$store.queue.items.length);
      }
      
      this.dragOverIdx = newOverIdx;
    },
    
    handleAutoScroll(y, container) {
      if (!container) {
        this.stopAutoScroll();
        return;
      }
      
      const rect = container.getBoundingClientRect();
      const scrollZone = 50;
      const scrollSpeed = 10;
      
      if (y < rect.top + scrollZone && container.scrollTop > 0) {
        this.startAutoScroll(container, -scrollSpeed, y);
      } else if (y > rect.bottom - scrollZone && container.scrollTop < container.scrollHeight - container.clientHeight) {
        this.startAutoScroll(container, scrollSpeed, y);
      } else {
        this.stopAutoScroll();
      }
    },
    
    startAutoScroll(container, speed, y) {
      if (this.scrollInterval) return;
      
      this.scrollInterval = setInterval(() => {
        container.scrollTop += speed;
        this.updateDropTarget(y);
      }, 16);
    },
    
    stopAutoScroll() {
      if (this.scrollInterval) {
        clearInterval(this.scrollInterval);
        this.scrollInterval = null;
      }
    },
    
    reorder(fromIdx, toIdx) {
      const queue = this.$store.queue;
      const items = [...queue.items];
      
      let actualToIdx = toIdx;
      if (fromIdx < toIdx) {
        actualToIdx = toIdx - 1;
      }
      
      if (fromIdx === actualToIdx) return;
      
      const [moved] = items.splice(fromIdx, 1);
      items.splice(actualToIdx, 0, moved);
      
      let newCurrentIndex = queue.currentIndex;
      if (fromIdx === queue.currentIndex) {
        newCurrentIndex = actualToIdx;
      } else if (fromIdx < queue.currentIndex && actualToIdx >= queue.currentIndex) {
        newCurrentIndex--;
      } else if (fromIdx > queue.currentIndex && actualToIdx <= queue.currentIndex) {
        newCurrentIndex++;
      }
      
      queue.items = items;
      queue.currentIndex = newCurrentIndex;
      queue.save();
    },
    
    isDragging(idx) {
      return this.dragging === idx;
    },
    
    isOtherDragging(idx) {
      return this.dragging !== null && this.dragging !== idx;
    },
    
    getShiftDirection(idx) {
      if (this.dragging === null || this.dragOverIdx === null) return 'none';
      if (idx === this.dragging) return 'none';
      
      const dragIdx = this.dragging;
      const overIdx = this.dragOverIdx;
      
      if (dragIdx < overIdx) {
        if (idx > dragIdx && idx < overIdx) {
          return 'up';
        }
      } else {
        if (idx >= overIdx && idx < dragIdx) {
          return 'down';
        }
      }
      
      return 'none';
    },
    
    getDragTransform() {
      if (this.dragging === null) return '';
      const container = this.$refs.sortableContainer;
      if (!container) return '';
      
      const items = container.querySelectorAll('.queue-item-wrapper');
      const draggedItem = items[this.dragging];
      if (!draggedItem) return '';
      
      const rect = draggedItem.getBoundingClientRect();
      const offsetY = this.dragY - (rect.top + rect.height / 2);
      
      return `translateY(${offsetY}px)`;
    },
  }));
}

export default createNowPlayingView;
